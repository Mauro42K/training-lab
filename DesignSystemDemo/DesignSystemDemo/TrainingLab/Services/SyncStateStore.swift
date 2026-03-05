import Foundation
import SwiftData

@MainActor
final class SyncStateStore {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func loadOrCreate() throws -> CachedSyncState {
        let descriptor = FetchDescriptor<CachedSyncState>()
        if let existing = try modelContext.fetch(descriptor).first {
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
    }

    func recordSuccessfulIngest(at date: Date) async throws {
        let state = try loadOrCreate()
        state.lastSuccessfulIngestAt = date
        state.syncStatusRaw = "idle"
        try modelContext.save()
    }

    func recordAPIRefresh(at date: Date) async throws {
        let state = try loadOrCreate()
        state.lastAPIRefreshAt = date
        try modelContext.save()
    }

    func recordError(_ message: String?) async throws {
        let state = try loadOrCreate()
        state.lastError = message
        if message != nil {
            state.syncStatusRaw = "error"
        }
        try modelContext.save()
    }
}
