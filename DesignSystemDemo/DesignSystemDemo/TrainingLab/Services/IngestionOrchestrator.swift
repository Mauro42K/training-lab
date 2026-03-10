import CryptoKit
import Foundation
import OSLog

@MainActor
final class IngestionOrchestrator {
    private let ingestBatchSize = 400
    #if DEBUG
    private let logger = Logger(subsystem: "com.traininglab.designsystemdemo", category: "ingest")
    private let isoFormatter = ISO8601DateFormatter()
    #endif

    private let healthKitClient: any HealthKitClient
    private let apiClient: any APIClient
    private let syncStateStore: SyncStateStore
    private let workoutsRepository: WorkoutsRepository
    private let dailyRepository: DailyRepository
    private let trainingLoadRepository: TrainingLoadRepository

    init(
        healthKitClient: any HealthKitClient,
        apiClient: any APIClient,
        syncStateStore: SyncStateStore,
        workoutsRepository: WorkoutsRepository,
        dailyRepository: DailyRepository,
        trainingLoadRepository: TrainingLoadRepository
    ) {
        self.healthKitClient = healthKitClient
        self.apiClient = apiClient
        self.syncStateStore = syncStateStore
        self.workoutsRepository = workoutsRepository
        self.dailyRepository = dailyRepository
        self.trainingLoadRepository = trainingLoadRepository
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

            let syncState = try syncStateStore.loadOrCreate()
            let isIncremental = syncState.hasCompletedRealHealthKitIngest
            let effectiveSince: Date? = isIncremental ? syncState.lastSuccessfulIngestAt : nil
            #if DEBUG
            logger.log("sync_mode=\(isIncremental ? "incremental" : "bootstrap", privacy: .public) effective_since=\(self.debugDateString(effectiveSince), privacy: .public)")
            #endif
            let workouts = try await healthKitClient.fetchWorkouts(since: effectiveSince)
            let normalizedWorkouts = normalizedWorkoutsForIngest(workouts)
            #if DEBUG
            let batchCount = normalizedWorkouts.isEmpty ? 0 : ((normalizedWorkouts.count + ingestBatchSize - 1) / ingestBatchSize)
            logger.log("workouts raw_count=\(workouts.count) normalized_count=\(normalizedWorkouts.count) batch_count=\(batchCount)")
            #endif

            if !normalizedWorkouts.isEmpty {
                for (index, batch) in normalizedWorkouts.chunked(into: ingestBatchSize).enumerated() {
                    let payload = WorkoutIngestDTO(workouts: batch)
                    let idempotencyKey = try makeIdempotencyKey(payload)
                    #if DEBUG
                    logger.log("ingest batch_start index=\(index + 1) size=\(batch.count) idempotency=\(self.shortenedDigest(idempotencyKey), privacy: .public)")
                    #endif
                    let response = try await apiClient.ingestWorkouts(idempotencyKey: idempotencyKey, payload: payload)
                    #if DEBUG
                    logger.log("ingest batch_success index=\(index + 1) accepted=\(response.accepted) updated=\(response.updated) replay=\(response.idempotentReplay)")
                    #endif
                }
            }

            let refreshFrom = Calendar.current.date(byAdding: .day, value: -30, to: now) ?? now
            #if DEBUG
            logger.log("refresh start from=\(self.debugDateString(refreshFrom), privacy: .public) to=\(self.debugDateString(now), privacy: .public)")
            #endif
            _ = try await workoutsRepository.getWorkouts(from: refreshFrom, to: now, sport: nil)
            _ = try await dailyRepository.getDaily(from: refreshFrom, to: now)

            try await syncStateStore.recordSuccessfulIngest(at: now)
            try await syncStateStore.markRealHealthKitIngestCompleted()
            try await syncStateStore.recordAPIRefresh(at: now)
            try await syncStateStore.recordError(nil)
            try updateSyncState(healthAuthStatusRaw: "authorized", syncStatusRaw: "ready")
            #if DEBUG
            let refreshedState = try? syncStateStore.loadOrCreate()
            logger.log(
                "sync complete last_successful=\(self.debugDateString(refreshedState?.lastSuccessfulIngestAt), privacy: .public) has_real_ingest=\(refreshedState?.hasCompletedRealHealthKitIngest ?? false) sync_status=\(refreshedState?.syncStatusRaw ?? "unknown", privacy: .public)"
            )
            #endif
        } catch {
            let message = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
            #if DEBUG
            logger.error("sync failed error=\(message, privacy: .public)")
            #endif
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

    private func normalizedWorkoutsForIngest(_ workouts: [WorkoutDTO]) -> [WorkoutDTO] {
        var byUUID: [String: WorkoutDTO] = [:]
        byUUID.reserveCapacity(workouts.count)

        for workout in workouts {
            if let existing = byUUID[workout.uuid], existing.end >= workout.end {
                continue
            }
            byUUID[workout.uuid] = workout
        }

        return byUUID.values.sorted {
            if $0.start == $1.start {
                return $0.uuid < $1.uuid
            }
            return $0.start < $1.start
        }
    }

    private func updateSyncState(healthAuthStatusRaw: String?, syncStatusRaw: String?) throws {
        let state = try syncStateStore.loadOrCreate()
        if let healthAuthStatusRaw {
            state.healthAuthStatusRaw = healthAuthStatusRaw
        }
        if let syncStatusRaw {
            state.syncStatusRaw = syncStatusRaw
        }
        #if DEBUG
        logger.log(
            "sync_state update health_auth=\(state.healthAuthStatusRaw, privacy: .public) sync_status=\(state.syncStatusRaw, privacy: .public)"
        )
        #endif
        // Persist through existing store API.
        Task { try? await syncStateStore.recordAPIRefresh(at: Date()) }
    }

    #if DEBUG
    private func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        return isoFormatter.string(from: date)
    }

    private func shortenedDigest(_ value: String) -> String {
        if value.count <= 16 {
            return value
        }
        return "\(value.prefix(8))...\(value.suffix(6))"
    }
    #endif
}

private extension Array {
    func chunked(into batchSize: Int) -> [[Element]] {
        guard batchSize > 0, !isEmpty else {
            return isEmpty ? [] : [self]
        }

        var chunks: [[Element]] = []
        chunks.reserveCapacity((count + batchSize - 1) / batchSize)

        var index = startIndex
        while index < endIndex {
            let end = self.index(index, offsetBy: batchSize, limitedBy: endIndex) ?? endIndex
            chunks.append(Array(self[index..<end]))
            index = end
        }
        return chunks
    }
}
