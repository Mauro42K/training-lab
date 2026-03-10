import Foundation
import SwiftData

@Model
final class CachedSyncState {
    var lastSuccessfulIngestAt: Date?
    var lastIngestAttemptAt: Date?
    var lastAPIRefreshAt: Date?
    var lastError: String?
    var healthAuthStatusRaw: String
    var syncStatusRaw: String
    var hasCompletedRealHealthKitIngest: Bool

    init(
        lastSuccessfulIngestAt: Date? = nil,
        lastIngestAttemptAt: Date? = nil,
        lastAPIRefreshAt: Date? = nil,
        lastError: String? = nil,
        healthAuthStatusRaw: String = "unknown",
        syncStatusRaw: String = "idle",
        hasCompletedRealHealthKitIngest: Bool = false
    ) {
        self.lastSuccessfulIngestAt = lastSuccessfulIngestAt
        self.lastIngestAttemptAt = lastIngestAttemptAt
        self.lastAPIRefreshAt = lastAPIRefreshAt
        self.lastError = lastError
        self.healthAuthStatusRaw = healthAuthStatusRaw
        self.syncStatusRaw = syncStatusRaw
        self.hasCompletedRealHealthKitIngest = hasCompletedRealHealthKitIngest
    }
}
