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
            let workoutSync = try await syncWorkouts(syncState: syncState)
            let physiologySync = try await syncPhysiology(syncState: syncState, now: now)

            let refreshFrom = refreshStartDate(now: now, workoutSync: workoutSync, physiologySync: physiologySync)
            #if DEBUG
            logger.log("refresh start from=\(self.debugDateString(refreshFrom), privacy: .public) to=\(self.debugDateString(now), privacy: .public)")
            #endif
            _ = try await workoutsRepository.getWorkouts(from: refreshFrom, to: now, sport: nil)
            _ = try await dailyRepository.getDaily(from: refreshFrom, to: now)
            _ = trainingLoadRepository

            try await syncStateStore.recordSuccessfulWorkoutIngest(
                at: now,
                mode: workoutSync.mode.rawValue,
                sampleCount: workoutSync.sampleCount,
                latestSampleAt: workoutSync.latestSampleAt,
                bootstrapCompleted: workoutSync.bootstrapCompleted
            )
            try await syncStateStore.recordSuccessfulPhysiologyIngest(
                at: now,
                mode: physiologySync.mode.rawValue,
                sleepSampleCount: physiologySync.sleepSampleCount,
                recoverySampleCount: physiologySync.recoverySampleCount,
                latestSleepSampleAt: physiologySync.latestSleepSampleAt,
                latestRecoverySampleAt: physiologySync.latestRecoverySampleAt,
                bootstrapCompleted: physiologySync.bootstrapCompleted
            )
            try await syncStateStore.recordAPIRefresh(at: now)
            try await syncStateStore.recordError(nil)
            try updateSyncState(healthAuthStatusRaw: "authorized", syncStatusRaw: "ready")
            #if DEBUG
            let refreshedState = try? syncStateStore.loadOrCreate()
            logger.log(
                "sync complete last_successful=\(self.debugDateString(refreshedState?.lastSuccessfulIngestAt), privacy: .public) workout_mode=\(refreshedState?.lastWorkoutSyncModeRaw ?? "unknown", privacy: .public) workout_samples=\(refreshedState?.lastWorkoutSampleCount ?? 0) physiology_mode=\(refreshedState?.lastPhysiologySyncModeRaw ?? "unknown", privacy: .public) sleep_samples=\(refreshedState?.lastPhysiologySleepSampleCount ?? 0) recovery_samples=\(refreshedState?.lastPhysiologyRecoverySampleCount ?? 0) sync_status=\(refreshedState?.syncStatusRaw ?? "unknown", privacy: .public)"
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

    private func syncWorkouts(syncState: CachedSyncState) async throws -> WorkoutSyncSnapshot {
        let isIncremental = syncState.hasCompletedRealHealthKitIngest ?? false
        let effectiveSince: Date? = isIncremental ? syncState.lastSuccessfulIngestAt : nil
        let mode: SyncMode = isIncremental ? .incremental : .bootstrap
        #if DEBUG
        logger.log(
            "workout_sync mode=\(mode.rawValue, privacy: .public) effective_since=\(self.debugDateString(effectiveSince), privacy: .public)"
        )
        #endif

        let workouts = try await healthKitClient.fetchWorkouts(since: effectiveSince)
        let normalizedWorkouts = normalizedWorkoutsForIngest(workouts)
        #if DEBUG
        let batchCount = normalizedWorkouts.isEmpty ? 0 : ((normalizedWorkouts.count + ingestBatchSize - 1) / ingestBatchSize)
        logger.log("workout_sync raw_count=\(workouts.count) normalized_count=\(normalizedWorkouts.count) batch_count=\(batchCount)")
        #endif

        if !normalizedWorkouts.isEmpty {
            for (index, batch) in normalizedWorkouts.chunked(into: ingestBatchSize).enumerated() {
                let payload = WorkoutIngestDTO(workouts: batch)
                let idempotencyKey = try makeIdempotencyKey(prefix: "hk-workouts", payload: payload)
                #if DEBUG
                logger.log(
                    "workout_sync batch_start index=\(index + 1) size=\(batch.count) idempotency=\(self.shortenedDigest(idempotencyKey), privacy: .public)"
                )
                #endif
                let response = try await apiClient.ingestWorkouts(idempotencyKey: idempotencyKey, payload: payload)
                #if DEBUG
                logger.log(
                    "workout_sync batch_success index=\(index + 1) accepted=\(response.accepted) updated=\(response.updated) replay=\(response.idempotentReplay)"
                )
                #endif
            }
        }

        #if DEBUG
        if normalizedWorkouts.isEmpty {
            logger.log("workout_sync result empty=true mode=\(mode.rawValue, privacy: .public)")
        }
        #endif

        return WorkoutSyncSnapshot(
            mode: mode,
            effectiveSince: effectiveSince,
            sampleCount: normalizedWorkouts.count,
            latestSampleAt: normalizedWorkouts.last?.end,
            bootstrapCompleted: !isIncremental
        )
    }

    private func syncPhysiology(syncState: CachedSyncState, now: Date) async throws -> PhysiologySyncSnapshot {
        let isIncremental = syncState.hasCompletedPhysiologyIngest ?? false
        let effectiveSince: Date? = isIncremental ? syncState.lastSuccessfulPhysiologyIngestAt : nil
        let mode: SyncMode = isIncremental ? .incremental : .bootstrap
        try await syncStateStore.recordPhysiologyIngestAttempt(at: now, mode: mode.rawValue)
        #if DEBUG
        logger.log("physiology_sync mode=\(mode.rawValue, privacy: .public) effective_since=\(self.debugDateString(effectiveSince), privacy: .public)")
        #endif

        let sleepSessions = normalizedSleepSessionsForIngest(try await healthKitClient.fetchSleepSessions(since: effectiveSince))
        let recoverySignals = normalizedRecoverySignalsForIngest(try await healthKitClient.fetchRecoverySignals(since: effectiveSince))
        #if DEBUG
        logger.log(
            "physiology_sync fetched sleep_count=\(sleepSessions.count) recovery_count=\(recoverySignals.count) latest_sleep=\(self.debugDateString(sleepSessions.last?.end), privacy: .public) latest_recovery=\(self.debugDateString(recoverySignals.last?.measuredAt), privacy: .public)"
        )
        if sleepSessions.isEmpty && recoverySignals.isEmpty {
            logger.log("physiology_sync result empty=true mode=\(mode.rawValue, privacy: .public)")
        }
        #endif

        try await ingestSleepSessions(sleepSessions)
        try await ingestRecoverySignals(recoverySignals)

        return PhysiologySyncSnapshot(
            mode: mode,
            effectiveSince: effectiveSince,
            sleepSampleCount: sleepSessions.count,
            recoverySampleCount: recoverySignals.count,
            latestSleepSampleAt: sleepSessions.last?.end,
            latestRecoverySampleAt: recoverySignals.last?.measuredAt,
            bootstrapCompleted: !isIncremental
        )
    }

    private func ingestSleepSessions(_ sleepSessions: [SleepSessionIngestItemDTO]) async throws {
        guard !sleepSessions.isEmpty else {
            #if DEBUG
            logger.log("physiology_sync sleep_ingest skipped reason=empty")
            #endif
            return
        }

        for (index, batch) in sleepSessions.chunked(into: ingestBatchSize).enumerated() {
            let payload = SleepSessionsIngestDTO(timezone: timeZoneIdentifier, sleepSessions: batch)
            let idempotencyKey = try makeIdempotencyKey(prefix: "hk-sleep", payload: payload)
            #if DEBUG
            logger.log(
                "physiology_sync sleep_batch_start index=\(index + 1) size=\(batch.count) idempotency=\(self.shortenedDigest(idempotencyKey), privacy: .public) timezone=\(self.timeZoneIdentifier, privacy: .public)"
            )
            #endif
            let response = try await apiClient.ingestSleepSessions(idempotencyKey: idempotencyKey, payload: payload)
            #if DEBUG
            logger.log(
                "physiology_sync sleep_batch_success index=\(index + 1) accepted=\(response.accepted) updated=\(response.updated) replay=\(response.idempotentReplay) rebuilt_dates=\(response.rebuiltDates ?? 0) invalidated_daily_recovery_dates=\(response.invalidatedDailyRecoveryDates ?? 0)"
            )
            #endif
        }
    }

    private func ingestRecoverySignals(_ recoverySignals: [RecoverySignalIngestItemDTO]) async throws {
        guard !recoverySignals.isEmpty else {
            #if DEBUG
            logger.log("physiology_sync recovery_ingest skipped reason=empty")
            #endif
            return
        }

        for (index, batch) in recoverySignals.chunked(into: ingestBatchSize).enumerated() {
            let payload = RecoverySignalsIngestDTO(timezone: timeZoneIdentifier, recoverySignals: batch)
            let idempotencyKey = try makeIdempotencyKey(prefix: "hk-recovery", payload: payload)
            #if DEBUG
            logger.log(
                "physiology_sync recovery_batch_start index=\(index + 1) size=\(batch.count) idempotency=\(self.shortenedDigest(idempotencyKey), privacy: .public) timezone=\(self.timeZoneIdentifier, privacy: .public)"
            )
            #endif
            let response = try await apiClient.ingestRecoverySignals(idempotencyKey: idempotencyKey, payload: payload)
            #if DEBUG
            logger.log(
                "physiology_sync recovery_batch_success index=\(index + 1) accepted=\(response.accepted) updated=\(response.updated) replay=\(response.idempotentReplay) rebuilt_dates=\(response.rebuiltDates ?? 0) rebuilt_daily_recovery_rows=\(response.rebuiltDailyRecoveryRows ?? 0)"
            )
            #endif
        }
    }

    private func makeIdempotencyKey<Payload: Encodable>(prefix: String, payload: Payload) throws -> String {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(payload)
        let digest = SHA256.hash(data: data)
        let hex = digest.map { String(format: "%02x", $0) }.joined()
        return "\(prefix)-\(hex)"
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

    private func normalizedSleepSessionsForIngest(_ sessions: [HealthKitSleepSessionDTO]) -> [SleepSessionIngestItemDTO] {
        var byUUID: [String: HealthKitSleepSessionDTO] = [:]
        byUUID.reserveCapacity(sessions.count)

        for session in sessions {
            guard session.end >= session.start else {
                continue
            }
            if let existing = byUUID[session.uuid], existing.end >= session.end {
                continue
            }
            byUUID[session.uuid] = session
        }

        return byUUID.values.sorted {
            if $0.start == $1.start {
                return $0.uuid < $1.uuid
            }
            return $0.start < $1.start
        }.map {
            SleepSessionIngestItemDTO(
                healthkitSleepUUID: $0.uuid,
                start: $0.start,
                end: $0.end,
                categoryValue: $0.categoryValue,
                sourceBundleId: $0.sourceBundleId,
                sourceCount: $0.sourceCount,
                hasMixedSources: $0.hasMixedSources,
                primaryDeviceName: $0.primaryDeviceName
            )
        }
    }

    private func normalizedRecoverySignalsForIngest(_ signals: [HealthKitRecoverySignalDTO]) -> [RecoverySignalIngestItemDTO] {
        var byUUID: [String: HealthKitRecoverySignalDTO] = [:]
        byUUID.reserveCapacity(signals.count)

        for signal in signals {
            if let existing = byUUID[signal.uuid], existing.measuredAt >= signal.measuredAt {
                continue
            }
            byUUID[signal.uuid] = signal
        }

        return byUUID.values.sorted {
            if $0.measuredAt == $1.measuredAt {
                return $0.uuid < $1.uuid
            }
            return $0.measuredAt < $1.measuredAt
        }.map {
            RecoverySignalIngestItemDTO(
                healthkitSignalUUID: $0.uuid,
                signalType: $0.signalType,
                measuredAt: $0.measuredAt,
                value: $0.value,
                sourceBundleId: $0.sourceBundleId,
                sourceCount: $0.sourceCount,
                hasMixedSources: $0.hasMixedSources,
                primaryDeviceName: $0.primaryDeviceName
            )
        }
    }

    private func refreshStartDate(
        now: Date,
        workoutSync: WorkoutSyncSnapshot,
        physiologySync: PhysiologySyncSnapshot
    ) -> Date {
        let defaultRefreshFrom = Calendar.current.date(byAdding: .day, value: -30, to: now) ?? now
        let candidates = [defaultRefreshFrom, workoutSync.effectiveSince, physiologySync.effectiveSince].compactMap { $0 }
        return candidates.min() ?? defaultRefreshFrom
    }

    private var timeZoneIdentifier: String {
        let autoupdating = TimeZone.autoupdatingCurrent.identifier
        if !autoupdating.isEmpty {
            return autoupdating
        }
        let current = TimeZone.current.identifier
        return current.isEmpty ? "UTC" : current
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

private struct WorkoutSyncSnapshot {
    let mode: SyncMode
    let effectiveSince: Date?
    let sampleCount: Int
    let latestSampleAt: Date?
    let bootstrapCompleted: Bool
}

private struct PhysiologySyncSnapshot {
    let mode: SyncMode
    let effectiveSince: Date?
    let sleepSampleCount: Int
    let recoverySampleCount: Int
    let latestSleepSampleAt: Date?
    let latestRecoverySampleAt: Date?
    let bootstrapCompleted: Bool
}

private enum SyncMode: String {
    case bootstrap
    case incremental
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
