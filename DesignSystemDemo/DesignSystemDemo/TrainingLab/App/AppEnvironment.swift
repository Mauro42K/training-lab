import Foundation
import SwiftData

struct AppEnvironment {
    private enum RuntimeConfigKey {
        static let bundleAPIBaseURL = "TrainingLabAPIBaseURL"
        static let bundleAPIKey = "TrainingLabAPIKey"
        static let bundleRuntimeEnvironment = "TrainingLabRuntimeEnvironment"
        static let envAPIBaseURL = "TRAINING_LAB_API_BASE_URL"
        static let envAPIKey = "TRAINING_LAB_API_KEY"
        static let envRuntimeEnvironment = "TRAINING_LAB_RUNTIME_ENV"
    }

    enum RuntimeEnvironment: String {
        case production
        case staging
        case local

        init(rawValueOrNil: String?, fallbackBaseURL: URL) {
            if let inferred = Self.inferredEnvironment(for: fallbackBaseURL) {
                self = inferred
                return
            }

            if let normalized = rawValueOrNil?.normalizedRuntimeConfigValue.lowercased(),
               let explicit = RuntimeEnvironment(rawValue: normalized) {
                self = explicit
                return
            }

            self = .production
        }

        var badgeLabel: String {
            rawValue.uppercased()
        }

        private static func inferredEnvironment(for baseURL: URL) -> RuntimeEnvironment? {
            let host = baseURL.host?.lowercased() ?? ""
            if host == "127.0.0.1" || host == "localhost" {
                return .local
            }
            if host.contains("staging") || host.contains("sslip.io") {
                return .staging
            }
            if host == "api.training-lab.mauro42k.com" {
                return .production
            }
            return nil
        }
    }

    let apiBaseURL: URL
    let apiKey: String
    let runtimeEnvironment: RuntimeEnvironment

    let modelContainer: ModelContainer
    let apiClient: any APIClient
    let healthKitClient: any HealthKitClient
    let syncStateStore: SyncStateStore
    let workoutsRepository: WorkoutsRepository
    let dailyRepository: DailyRepository
    let homeSummaryRepository: HomeSummaryRepository
    let trainingLoadRepository: TrainingLoadRepository
    let ingestionOrchestrator: IngestionOrchestrator

    @MainActor
    static func live() -> AppEnvironment {
        let defaultBaseURL = URL(string: "https://api.training-lab.mauro42k.com")!

        let bundleBaseURL = Bundle.main.runtimeConfigValue(forKey: RuntimeConfigKey.bundleAPIBaseURL)
            .flatMap(URL.init(string:))
        let envBaseURL = ProcessInfo.processInfo.environment[RuntimeConfigKey.envAPIBaseURL]
            .map { $0.normalizedRuntimeConfigValue }
            .flatMap(URL.init(string:))
        let baseURL = envBaseURL ?? bundleBaseURL ?? defaultBaseURL

        let bundleRuntimeEnvironment = Bundle.main.runtimeConfigValue(forKey: RuntimeConfigKey.bundleRuntimeEnvironment)
        let envRuntimeEnvironment = ProcessInfo.processInfo.environment[RuntimeConfigKey.envRuntimeEnvironment]
        let runtimeEnvironment = RuntimeEnvironment(
            rawValueOrNil: envRuntimeEnvironment ?? bundleRuntimeEnvironment,
            fallbackBaseURL: baseURL
        )

        let bundleAPIKey = Bundle.main.runtimeConfigValue(forKey: RuntimeConfigKey.bundleAPIKey) ?? ""
        let envAPIKey = ProcessInfo.processInfo.environment[RuntimeConfigKey.envAPIKey]?.normalizedRuntimeConfigValue ?? ""
        let key = envAPIKey.isEmpty ? bundleAPIKey : envAPIKey

        let container = try! ModelContainer(
            for: CachedWorkout.self,
            CachedDailySummary.self,
            CachedTrainingLoadPoint.self,
            CachedSyncState.self
        )
        let modelContext = ModelContext(container)

        let apiClient: any APIClient
        if key.isEmpty {
            apiClient = MissingAPIKeyAPIClient()
        } else {
            let config = URLSessionAPIClient.Configuration(baseURL: baseURL, apiKey: key)
            apiClient = URLSessionAPIClient(configuration: config)
        }

        #if os(iOS) && canImport(HealthKit)
        let healthKitClient: any HealthKitClient = HealthKitClientLive()
        #else
        let healthKitClient: any HealthKitClient = HealthKitClientUnsupported()
        #endif

        let syncStateStore = SyncStateStore(modelContext: modelContext)
        let workoutsRepository = WorkoutsRepository(apiClient: apiClient, modelContext: modelContext)
        let dailyRepository = DailyRepository(apiClient: apiClient, modelContext: modelContext)
        let homeSummaryRepository = HomeSummaryRepository(apiClient: apiClient)
        let trainingLoadRepository = TrainingLoadRepository(
            apiClient: apiClient,
            modelContext: modelContext,
            baseURL: baseURL,
            cacheScope: cacheScope(for: baseURL)
        )
        let ingestionOrchestrator = IngestionOrchestrator(
            healthKitClient: healthKitClient,
            apiClient: apiClient,
            syncStateStore: syncStateStore,
            workoutsRepository: workoutsRepository,
            dailyRepository: dailyRepository,
            trainingLoadRepository: trainingLoadRepository
        )

        return AppEnvironment(
            apiBaseURL: baseURL,
            apiKey: key,
            runtimeEnvironment: runtimeEnvironment,
            modelContainer: container,
            apiClient: apiClient,
            healthKitClient: healthKitClient,
            syncStateStore: syncStateStore,
            workoutsRepository: workoutsRepository,
            dailyRepository: dailyRepository,
            homeSummaryRepository: homeSummaryRepository,
            trainingLoadRepository: trainingLoadRepository,
            ingestionOrchestrator: ingestionOrchestrator
        )
    }

    @MainActor
    static func stub() -> AppEnvironment {
        live()
    }

    private static func cacheScope(for baseURL: URL) -> String {
        let normalized = baseURL.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        return normalized.lowercased()
    }
}

private extension Bundle {
    func runtimeConfigValue(forKey key: String) -> String? {
        guard let rawValue = object(forInfoDictionaryKey: key) as? String else {
            return nil
        }
        let normalized = rawValue.normalizedRuntimeConfigValue
        return normalized.isEmpty ? nil : normalized
    }
}

private extension String {
    var normalizedRuntimeConfigValue: String {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count >= 2, trimmed.hasPrefix("\""), trimmed.hasSuffix("\"") else {
            return trimmed
        }
        return String(trimmed.dropFirst().dropLast())
    }
}

enum AppEnvironmentError: Error, LocalizedError {
    case missingAPIKey

    var errorDescription: String? {
        switch self {
        case .missingAPIKey:
            "missing api key"
        }
    }
}

private struct MissingAPIKeyAPIClient: APIClient {
    func ingestWorkouts(idempotencyKey: String, payload: WorkoutIngestDTO) async throws -> IngestResponseDTO {
        _ = idempotencyKey
        _ = payload
        throw AppEnvironmentError.missingAPIKey
    }

    func ingestSleepSessions(idempotencyKey: String, payload: SleepSessionsIngestDTO) async throws -> IngestResponseDTO {
        _ = idempotencyKey
        _ = payload
        throw AppEnvironmentError.missingAPIKey
    }

    func ingestRecoverySignals(idempotencyKey: String, payload: RecoverySignalsIngestDTO) async throws -> IngestResponseDTO {
        _ = idempotencyKey
        _ = payload
        throw AppEnvironmentError.missingAPIKey
    }

    func fetchWorkouts(from: Date, to: Date, sport: SportType?) async throws -> [WorkoutDTO] {
        _ = from
        _ = to
        _ = sport
        throw AppEnvironmentError.missingAPIKey
    }

    func fetchDaily(from: Date, to: Date) async throws -> [DailyItemDTO] {
        _ = from
        _ = to
        throw AppEnvironmentError.missingAPIKey
    }

    func fetchHomeSummary(date: Date) async throws -> HomeSummaryDTO {
        _ = date
        throw AppEnvironmentError.missingAPIKey
    }

    func fetchTrainingLoad(days: Int, sport: TrainingLoadSportFilter) async throws -> TrainingLoadSummaryDTO {
        _ = days
        _ = sport
        throw AppEnvironmentError.missingAPIKey
    }
}
