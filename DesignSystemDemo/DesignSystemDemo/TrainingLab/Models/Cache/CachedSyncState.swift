import Foundation
import SwiftData

@Model
final class CachedSyncState {
    var lastSuccessfulIngestAt: Date?
    var lastIngestAttemptAt: Date?
    var lastWorkoutSampleAt: Date?
    var lastSuccessfulPhysiologyIngestAt: Date?
    var lastPhysiologyIngestAttemptAt: Date?
    var lastAPIRefreshAt: Date?
    var lastPhysiologySleepSampleAt: Date?
    var lastPhysiologyRecoverySampleAt: Date?
    var lastError: String?
    var healthAuthStatusRaw: String
    var syncStatusRaw: String
    var hasCompletedRealHealthKitIngest: Bool?
    var hasCompletedPhysiologyIngest: Bool?
    var lastWorkoutSyncModeRaw: String?
    var lastWorkoutSampleCount: Int?
    var lastPhysiologySyncModeRaw: String?
    var lastPhysiologySleepSampleCount: Int?
    var lastPhysiologyRecoverySampleCount: Int?

    init(
        lastSuccessfulIngestAt: Date? = nil,
        lastIngestAttemptAt: Date? = nil,
        lastWorkoutSampleAt: Date? = nil,
        lastSuccessfulPhysiologyIngestAt: Date? = nil,
        lastPhysiologyIngestAttemptAt: Date? = nil,
        lastAPIRefreshAt: Date? = nil,
        lastPhysiologySleepSampleAt: Date? = nil,
        lastPhysiologyRecoverySampleAt: Date? = nil,
        lastError: String? = nil,
        healthAuthStatusRaw: String = "unknown",
        syncStatusRaw: String = "idle",
        hasCompletedRealHealthKitIngest: Bool? = false,
        hasCompletedPhysiologyIngest: Bool? = false,
        lastWorkoutSyncModeRaw: String? = nil,
        lastWorkoutSampleCount: Int? = nil,
        lastPhysiologySyncModeRaw: String? = nil,
        lastPhysiologySleepSampleCount: Int? = nil,
        lastPhysiologyRecoverySampleCount: Int? = nil
    ) {
        self.lastSuccessfulIngestAt = lastSuccessfulIngestAt
        self.lastIngestAttemptAt = lastIngestAttemptAt
        self.lastWorkoutSampleAt = lastWorkoutSampleAt
        self.lastSuccessfulPhysiologyIngestAt = lastSuccessfulPhysiologyIngestAt
        self.lastPhysiologyIngestAttemptAt = lastPhysiologyIngestAttemptAt
        self.lastAPIRefreshAt = lastAPIRefreshAt
        self.lastPhysiologySleepSampleAt = lastPhysiologySleepSampleAt
        self.lastPhysiologyRecoverySampleAt = lastPhysiologyRecoverySampleAt
        self.lastError = lastError
        self.healthAuthStatusRaw = healthAuthStatusRaw
        self.syncStatusRaw = syncStatusRaw
        self.hasCompletedRealHealthKitIngest = hasCompletedRealHealthKitIngest
        self.hasCompletedPhysiologyIngest = hasCompletedPhysiologyIngest
        self.lastWorkoutSyncModeRaw = lastWorkoutSyncModeRaw
        self.lastWorkoutSampleCount = lastWorkoutSampleCount
        self.lastPhysiologySyncModeRaw = lastPhysiologySyncModeRaw
        self.lastPhysiologySleepSampleCount = lastPhysiologySleepSampleCount
        self.lastPhysiologyRecoverySampleCount = lastPhysiologyRecoverySampleCount
    }
}
