import CryptoKit
import Foundation

@MainActor
final class IngestionOrchestrator {
    private let healthKitClient: any HealthKitClient
    private let apiClient: any APIClient
    private let syncStateStore: SyncStateStore
    private let workoutsRepository: WorkoutsRepository
    private let dailyRepository: DailyRepository

    init(
        healthKitClient: any HealthKitClient,
        apiClient: any APIClient,
        syncStateStore: SyncStateStore,
        workoutsRepository: WorkoutsRepository,
        dailyRepository: DailyRepository
    ) {
        self.healthKitClient = healthKitClient
        self.apiClient = apiClient
        self.syncStateStore = syncStateStore
        self.workoutsRepository = workoutsRepository
        self.dailyRepository = dailyRepository
    }

    func runInitialSyncIfNeeded() async {
        let now = Date()

        do {
            try await syncStateStore.recordIngestAttempt(at: now)

            let authorized = try await healthKitClient.requestAuthorization()
            try updateSyncState(healthAuthStatusRaw: authorized ? "authorized" : "denied", syncStatusRaw: nil)

            guard authorized else {
                try await syncStateStore.recordError("HealthKit authorization required")
                return
            }

            let lastIngestDate = try syncStateStore.loadOrCreate().lastSuccessfulIngestAt
            let workouts = try await healthKitClient.fetchWorkouts(since: lastIngestDate)

            if !workouts.isEmpty {
                let payload = WorkoutIngestDTO(workouts: workouts)
                let idempotencyKey = try makeIdempotencyKey(payload)
                _ = try await apiClient.ingestWorkouts(idempotencyKey: idempotencyKey, payload: payload)
            }

            let refreshFrom = Calendar.current.date(byAdding: .day, value: -30, to: now) ?? now
            _ = try await workoutsRepository.getWorkouts(from: refreshFrom, to: now, sport: nil)
            _ = try await dailyRepository.getDaily(from: refreshFrom, to: now)

            try await syncStateStore.recordSuccessfulIngest(at: now)
            try await syncStateStore.recordAPIRefresh(at: now)
            try await syncStateStore.recordError(nil)
            try updateSyncState(healthAuthStatusRaw: "authorized", syncStatusRaw: "ready")
        } catch {
            let message = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
            try? await syncStateStore.recordError(message)

            if case HealthKitClientError.unsupported = error {
                try? updateSyncState(healthAuthStatusRaw: "unsupported", syncStatusRaw: "error")
            } else {
                try? updateSyncState(healthAuthStatusRaw: nil, syncStatusRaw: "error")
            }
        }
    }

    private func makeIdempotencyKey(_ payload: WorkoutIngestDTO) throws -> String {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(payload)
        let digest = SHA256.hash(data: data)
        let hex = digest.map { String(format: "%02x", $0) }.joined()
        return "hk-\(hex)"
    }

    private func updateSyncState(healthAuthStatusRaw: String?, syncStatusRaw: String?) throws {
        let state = try syncStateStore.loadOrCreate()
        if let healthAuthStatusRaw {
            state.healthAuthStatusRaw = healthAuthStatusRaw
        }
        if let syncStatusRaw {
            state.syncStatusRaw = syncStatusRaw
        }
        // Persist through existing store API.
        Task { try? await syncStateStore.recordAPIRefresh(at: Date()) }
    }
}
