import Foundation

protocol SyncClient: Sendable {
    func syncRecentWorkouts() async throws
}

struct PlaceholderSyncClient: SyncClient {
    let syncStateStore: SyncStateStore

    func syncRecentWorkouts() async throws {
        try await syncStateStore.recordIngestAttempt(at: Date())
        try await syncStateStore.recordSuccessfulIngest(at: Date())
        try await syncStateStore.recordError(nil)
    }
}
