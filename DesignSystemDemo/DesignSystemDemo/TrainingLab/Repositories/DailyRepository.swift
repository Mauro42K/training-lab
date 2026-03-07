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

@MainActor
final class TrainingLoadRepository {
    private let apiClient: any APIClient
    private let modelContext: ModelContext
    private let cacheScope: String
    private let baseURLForDebug: URL

    init(apiClient: any APIClient, modelContext: ModelContext, baseURL: URL, cacheScope: String) {
        self.apiClient = apiClient
        self.modelContext = modelContext
        self.baseURLForDebug = baseURL
        self.cacheScope = cacheScope
    }

    func getTrainingLoad(days: Int = 28, sport: TrainingLoadSportFilter) async throws -> [TrainingLoadItemDTO] {
        do {
            let remote = try await apiClient.fetchTrainingLoad(days: days, sport: sport)
            do {
                try replaceCache(for: sport, with: remote)
            } catch {
                throw RepositoryError.cacheWriteFailed(underlying: error)
            }
            return remote
        } catch {
            let cached = try fetchCached(days: days, sport: sport)
            if cached.isEmpty {
                #if DEBUG
                throw RepositoryError.networkAndNoCache(
                    underlying: TrainingLoadNetworkContextError(
                        underlying: error,
                        baseURL: baseURLForDebug,
                        sport: sport
                    )
                )
                #else
                throw RepositoryError.networkAndNoCache(underlying: error)
                #endif
            }
            return cached
        }
    }

    private func replaceCache(for sport: TrainingLoadSportFilter, with items: [TrainingLoadItemDTO]) throws {
        let scopedSportKey = scopedSportKey(for: sport)
        let predicate = #Predicate<CachedTrainingLoadPoint> { item in
            item.sportFilterRaw == scopedSportKey
        }
        let descriptor = FetchDescriptor<CachedTrainingLoadPoint>(predicate: predicate)
        let existing = try modelContext.fetch(descriptor)
        for item in existing {
            modelContext.delete(item)
        }

        for item in items {
            modelContext.insert(
                CachedTrainingLoadPoint(
                    date: item.date,
                    sportFilterRaw: scopedSportKey,
                    trimp: item.trimp,
                    updatedAt: Date()
                )
            )
        }

        try modelContext.save()
    }

    private func fetchCached(days: Int, sport: TrainingLoadSportFilter) throws -> [TrainingLoadItemDTO] {
        let scopedSportKey = scopedSportKey(for: sport)
        let predicate = #Predicate<CachedTrainingLoadPoint> { item in
            item.sportFilterRaw == scopedSportKey
        }
        let descriptor = FetchDescriptor<CachedTrainingLoadPoint>(
            predicate: predicate,
            sortBy: [SortDescriptor(\CachedTrainingLoadPoint.date)]
        )
        let cached = try modelContext.fetch(descriptor)
        let sliced = cached.suffix(max(days, 1))
        return sliced.map { item in
            TrainingLoadItemDTO(date: item.date, trimp: item.trimp)
        }
    }

    // Pragmatic namespace isolation without widening SwiftData model scope in Phase 4.1.
    private func scopedSportKey(for sport: TrainingLoadSportFilter) -> String {
        "\(cacheScope)|\(sport.rawValue)"
    }
}

private struct TrainingLoadNetworkContextError: LocalizedError {
    let underlying: Error
    let baseURL: URL
    let sport: TrainingLoadSportFilter

    var errorDescription: String? {
        "\(underlying.localizedDescription) [baseURL=\(baseURL.absoluteString) sport=\(sport.rawValue)]"
    }
}
