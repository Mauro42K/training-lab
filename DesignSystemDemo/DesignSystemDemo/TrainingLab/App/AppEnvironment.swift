import Foundation
import SwiftData

struct AppEnvironment {
    let apiBaseURL: URL
    let apiKey: String

    let modelContainer: ModelContainer
    let apiClient: any APIClient
    let healthKitClient: any HealthKitClient
    let syncStateStore: SyncStateStore
    let workoutsRepository: WorkoutsRepository
    let dailyRepository: DailyRepository
    let trainingLoadRepository: TrainingLoadRepository
    let ingestionOrchestrator: IngestionOrchestrator

    @MainActor
    static func live() -> AppEnvironment {
        let defaultBaseURL = URL(string: "https://api.training-lab.mauro42k.com")!
        let baseURL = ProcessInfo.processInfo.environment["TRAINING_LAB_API_BASE_URL"]
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .flatMap(URL.init(string:))
            ?? defaultBaseURL
        let key = ProcessInfo.processInfo.environment["TRAINING_LAB_API_KEY"]?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""

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
        let trainingLoadRepository = TrainingLoadRepository(apiClient: apiClient, modelContext: modelContext)
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
            modelContainer: container,
            apiClient: apiClient,
            healthKitClient: healthKitClient,
            syncStateStore: syncStateStore,
            workoutsRepository: workoutsRepository,
            dailyRepository: dailyRepository,
            trainingLoadRepository: trainingLoadRepository,
            ingestionOrchestrator: ingestionOrchestrator
        )
    }

    @MainActor
    static func stub() -> AppEnvironment {
        live()
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

    func fetchTrainingLoad(days: Int, sport: TrainingLoadSportFilter) async throws -> [TrainingLoadItemDTO] {
        _ = days
        _ = sport
        throw AppEnvironmentError.missingAPIKey
    }
}
