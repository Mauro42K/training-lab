import Foundation
import OSLog
import SwiftData

@MainActor
final class SyncStateStore {
    private let modelContext: ModelContext
    #if DEBUG
    private let logger = Logger(subsystem: "com.traininglab.designsystemdemo", category: "syncstate")
    private let isoFormatter = ISO8601DateFormatter()
    #endif

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func loadOrCreate() throws -> CachedSyncState {
        let descriptor = FetchDescriptor<CachedSyncState>()
        if let existing = try modelContext.fetch(descriptor).first {
            if existing.hasCompletedRealHealthKitIngest == nil {
                existing.hasCompletedRealHealthKitIngest = false
            }
            if existing.hasCompletedPhysiologyIngest == nil {
                existing.hasCompletedPhysiologyIngest = false
            }
            if existing.hasCompletedRealHealthKitIngest == nil || existing.hasCompletedPhysiologyIngest == nil {
                try modelContext.save()
            }
            return existing
        }

        let state = CachedSyncState()
        modelContext.insert(state)
        try modelContext.save()
        return state
    }

    func recordIngestAttempt(at date: Date) async throws {
        let state = try loadOrCreate()
        state.lastIngestAttemptAt = date
        state.syncStatusRaw = "syncing"
        try modelContext.save()
        #if DEBUG
        logger.log("recordIngestAttempt lastIngestAttemptAt=\(self.debugDateString(date), privacy: .public) syncStatus=\(state.syncStatusRaw, privacy: .public)")
        #endif
    }

    func recordSuccessfulIngest(at date: Date) async throws {
        let state = try loadOrCreate()
        state.lastSuccessfulIngestAt = date
        state.syncStatusRaw = "idle"
        try modelContext.save()
        #if DEBUG
        logger.log("recordSuccessfulIngest lastSuccessfulIngestAt=\(self.debugDateString(date), privacy: .public) syncStatus=\(state.syncStatusRaw, privacy: .public)")
        #endif
    }

    func recordSuccessfulWorkoutIngest(
        at date: Date,
        mode: String,
        sampleCount: Int,
        latestSampleAt: Date?,
        bootstrapCompleted: Bool
    ) async throws {
        let state = try loadOrCreate()
        state.lastSuccessfulIngestAt = date
        state.lastWorkoutSyncModeRaw = mode
        state.lastWorkoutSampleCount = sampleCount
        state.lastWorkoutSampleAt = latestSampleAt
        if bootstrapCompleted {
            state.hasCompletedRealHealthKitIngest = true
        }
        state.syncStatusRaw = "idle"
        try modelContext.save()
        #if DEBUG
        logger.log(
            "recordSuccessfulWorkoutIngest lastSuccessfulIngestAt=\(self.debugDateString(date), privacy: .public) mode=\(mode, privacy: .public) sample_count=\(sampleCount) latest_sample=\(self.debugDateString(latestSampleAt), privacy: .public) bootstrap_completed=\(bootstrapCompleted)"
        )
        #endif
    }

    func recordAPIRefresh(at date: Date) async throws {
        let state = try loadOrCreate()
        state.lastAPIRefreshAt = date
        try modelContext.save()
        #if DEBUG
        logger.log("recordAPIRefresh lastAPIRefreshAt=\(self.debugDateString(date), privacy: .public)")
        #endif
    }

    func markRealHealthKitIngestCompleted() async throws {
        let state = try loadOrCreate()
        state.hasCompletedRealHealthKitIngest = true
        try modelContext.save()
        #if DEBUG
        logger.log("markRealHealthKitIngestCompleted hasCompletedRealHealthKitIngest=\(state.hasCompletedRealHealthKitIngest ?? false)")
        #endif
    }

    func recordPhysiologyIngestAttempt(at date: Date, mode: String) async throws {
        let state = try loadOrCreate()
        state.lastPhysiologyIngestAttemptAt = date
        state.lastPhysiologySyncModeRaw = mode
        state.syncStatusRaw = "syncing"
        try modelContext.save()
        #if DEBUG
        logger.log(
            "recordPhysiologyIngestAttempt lastPhysiologyIngestAttemptAt=\(self.debugDateString(date), privacy: .public) mode=\(mode, privacy: .public)"
        )
        #endif
    }

    func recordSuccessfulPhysiologyIngest(
        at date: Date,
        mode: String,
        sleepSampleCount: Int,
        recoverySampleCount: Int,
        latestSleepSampleAt: Date?,
        latestRecoverySampleAt: Date?,
        bootstrapCompleted: Bool
    ) async throws {
        let state = try loadOrCreate()
        state.lastSuccessfulPhysiologyIngestAt = date
        state.lastPhysiologySyncModeRaw = mode
        state.lastPhysiologySleepSampleCount = sleepSampleCount
        state.lastPhysiologyRecoverySampleCount = recoverySampleCount
        state.lastPhysiologySleepSampleAt = latestSleepSampleAt
        state.lastPhysiologyRecoverySampleAt = latestRecoverySampleAt
        if bootstrapCompleted {
            state.hasCompletedPhysiologyIngest = true
        }
        try modelContext.save()
        #if DEBUG
        logger.log(
            "recordSuccessfulPhysiologyIngest lastSuccessfulPhysiologyIngestAt=\(self.debugDateString(date), privacy: .public) mode=\(mode, privacy: .public) sleep_count=\(sleepSampleCount) recovery_count=\(recoverySampleCount) latest_sleep=\(self.debugDateString(latestSleepSampleAt), privacy: .public) latest_recovery=\(self.debugDateString(latestRecoverySampleAt), privacy: .public) bootstrap_completed=\(bootstrapCompleted)"
        )
        #endif
    }

    func recordError(_ message: String?) async throws {
        let state = try loadOrCreate()
        state.lastError = message
        if message != nil {
            state.syncStatusRaw = "error"
        }
        try modelContext.save()
        #if DEBUG
        logger.log("recordError lastError=\((message ?? "nil"), privacy: .public) syncStatus=\(state.syncStatusRaw, privacy: .public)")
        #endif
    }

    #if DEBUG
    private func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        return isoFormatter.string(from: date)
    }
    #endif
}
