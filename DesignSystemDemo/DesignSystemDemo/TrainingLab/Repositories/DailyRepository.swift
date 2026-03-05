import Foundation
import SwiftData

@MainActor
final class DailyRepository {
    private let apiClient: any APIClient
    private let modelContext: ModelContext

    init(apiClient: any APIClient, modelContext: ModelContext) {
        self.apiClient = apiClient
        self.modelContext = modelContext
    }

    func getDaily(from: Date, to: Date) async throws -> [DailyItemDTO] {
        do {
            let remote = try await apiClient.fetchDaily(from: from, to: to)
            do {
                try replaceCache(from: from, to: to, with: remote)
            } catch {
                throw RepositoryError.cacheWriteFailed(underlying: error)
            }
            return remote
        } catch {
            let cached = try fetchCached(from: from, to: to)
            if cached.isEmpty {
                throw RepositoryError.networkAndNoCache(underlying: error)
            }
            return cached
        }
    }

    private func replaceCache(from: Date, to: Date, with items: [DailyItemDTO]) throws {
        let predicate = #Predicate<CachedDailySummary> { item in
            item.date >= from && item.date <= to
        }
        let descriptor = FetchDescriptor<CachedDailySummary>(predicate: predicate)
        let existing = try modelContext.fetch(descriptor)
        for item in existing {
            modelContext.delete(item)
        }

        for item in items {
            let cached = CachedDailySummary(
                date: item.date,
                workoutsCount: item.workoutsCount,
                durationSecTotal: item.durationSecTotal,
                distanceMTotal: item.distanceMTotal,
                energyKcalTotal: item.energyKcalTotal,
                updatedAt: Date()
            )
            modelContext.insert(cached)
        }

        try modelContext.save()
    }

    private func fetchCached(from: Date, to: Date) throws -> [DailyItemDTO] {
        let predicate = #Predicate<CachedDailySummary> { item in
            item.date >= from && item.date <= to
        }
        let descriptor = FetchDescriptor<CachedDailySummary>(predicate: predicate, sortBy: [SortDescriptor(\CachedDailySummary.date)])
        let cached = try modelContext.fetch(descriptor)

        return cached.map { item in
            DailyItemDTO(
                date: item.date,
                workoutsCount: item.workoutsCount,
                durationSecTotal: item.durationSecTotal,
                distanceMTotal: item.distanceMTotal,
                energyKcalTotal: item.energyKcalTotal
            )
        }
    }
}
