import Foundation
import OSLog
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
final class HomeSummaryRepository {
    private let apiClient: any APIClient

    init(apiClient: any APIClient) {
        self.apiClient = apiClient
    }

    func getHomeSummary(date: Date) async throws -> HomeSummaryDTO {
        try await apiClient.fetchHomeSummary(date: date)
    }
}

@MainActor
final class TrainingLoadRepository {
    #if DEBUG
    private let logger = Logger(subsystem: "com.traininglab.designsystemdemo", category: "trainingload")
    private let isoFormatter = ISO8601DateFormatter()
    #endif

    private struct LoadCapacitySemanticThresholds {
        let belowCapacityUpperBound = 0.85
        let withinRangeUpperBound = 1.0
        let nearLimitUpperBound = 1.15
    }

    private struct ReconstructedTrainingLoadSeries {
        let items: [TrainingLoadItemDTO]
        let latestCapacity: Double
        let latestFatigue: Double
    }

    private struct CachedTrainingLoadFetch {
        let summary: TrainingLoadSummaryDTO
        let latestCacheUpdatedAt: Date?
    }

    private static let fitnessWindowDays = 42
    private static let fatigueWindowDays = 7
    private static let loadCapacityThresholds = LoadCapacitySemanticThresholds()

    private let apiClient: any APIClient
    private let modelContext: ModelContext
    private let cacheScope: String
    private let baseURLForDebug: URL
    private let calendar = Calendar.current

    init(apiClient: any APIClient, modelContext: ModelContext, baseURL: URL, cacheScope: String) {
        self.apiClient = apiClient
        self.modelContext = modelContext
        self.baseURLForDebug = baseURL
        self.cacheScope = cacheScope
    }

    func getTrainingLoad(days: Int = 28, sport: TrainingLoadSportFilter) async throws -> TrainingLoadFetchResult {
        let requestStartedAt = Date()
        #if DEBUG
        debugEmit("fetch start baseURL=\(baseURLForDebug.absoluteString) sport=\(sport.rawValue) days=\(days)")
        #endif

        do {
            let remote = try await apiClient.fetchTrainingLoad(days: days, sport: sport)
            do {
                try replaceCache(for: sport, with: remote, cachedAt: requestStartedAt)
            } catch {
                throw RepositoryError.cacheWriteFailed(underlying: error)
            }
            let result = TrainingLoadFetchResult(
                summary: remote,
                freshness: TrainingLoadFreshness(
                    source: .remote,
                    baseURL: baseURLForDebug,
                    remoteAttempted: true,
                    remoteFailureDescription: nil,
                    fetchedAt: requestStartedAt,
                    latestPointDate: remote.items.last?.date,
                    cacheUpdatedAt: requestStartedAt
                )
            )
            #if DEBUG
            debugEmit(
                "fetch success source=remote baseURL=\(baseURLForDebug.absoluteString) latest_point=\(debugDateString(result.freshness.latestPointDate)) fetched_at=\(debugDateString(requestStartedAt))"
            )
            #endif
            return result
        } catch {
            #if DEBUG
            debugEmit(
                "fetch failure source=remote baseURL=\(baseURLForDebug.absoluteString) sport=\(sport.rawValue) error=\(error.localizedDescription)"
            )
            #endif
            let cached = try fetchCached(days: days, sport: sport)
            if cached.summary.items.isEmpty {
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
            let result = TrainingLoadFetchResult(
                summary: cached.summary,
                freshness: TrainingLoadFreshness(
                    source: .cache,
                    baseURL: baseURLForDebug,
                    remoteAttempted: true,
                    remoteFailureDescription: error.localizedDescription,
                    fetchedAt: requestStartedAt,
                    latestPointDate: cached.summary.items.last?.date,
                    cacheUpdatedAt: cached.latestCacheUpdatedAt
                )
            )
            #if DEBUG
            debugEmit(
                "fetch fallback source=cache baseURL=\(baseURLForDebug.absoluteString) latest_point=\(debugDateString(result.freshness.latestPointDate)) cache_updated_at=\(debugDateString(result.freshness.cacheUpdatedAt))"
            )
            #endif
            return result
        }
    }

    private func replaceCache(for sport: TrainingLoadSportFilter, with summary: TrainingLoadSummaryDTO, cachedAt: Date) throws {
        let scopedSportKey = scopedSportKey(for: sport)
        let predicate = #Predicate<CachedTrainingLoadPoint> { item in
            item.sportFilterRaw == scopedSportKey
        }
        let descriptor = FetchDescriptor<CachedTrainingLoadPoint>(predicate: predicate)
        let existing = try modelContext.fetch(descriptor)
        for item in existing {
            modelContext.delete(item)
        }

        for item in summary.items {
            modelContext.insert(
                CachedTrainingLoadPoint(
                    date: item.date,
                    sportFilterRaw: scopedSportKey,
                    trimp: item.trimp,
                    capacity: item.capacity,
                    historyStatusRaw: summary.historyStatus.rawValue,
                    semanticStateRaw: summary.semanticState?.rawValue,
                    latestLoad: summary.latestLoad,
                    latestCapacity: summary.latestCapacity,
                    updatedAt: cachedAt
                )
            )
        }

        try modelContext.save()
    }

    private func fetchCached(days: Int, sport: TrainingLoadSportFilter) throws -> CachedTrainingLoadFetch {
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
        guard let metadataSource = sliced.first ?? cached.first else {
            return CachedTrainingLoadFetch(
                summary: TrainingLoadSummaryDTO(
                    items: [],
                    historyStatus: .missing,
                    semanticState: nil,
                    latestLoad: 0,
                    latestCapacity: 0
                ),
                latestCacheUpdatedAt: nil
            )
        }

        let historyStatus = resolvedHistoryStatus(from: cached, metadataSource: metadataSource)
        let reconstructedSeries = reconstructedSeries(from: cached, sliced: Array(sliced))
        let latestLoad = metadataSource.latestLoad ?? sliced.last?.trimp ?? 0
        let latestCapacity = metadataSource.latestCapacity ?? reconstructedSeries.latestCapacity

        return CachedTrainingLoadFetch(
            summary: TrainingLoadSummaryDTO(
                items: reconstructedSeries.items,
                historyStatus: historyStatus,
                semanticState: resolvedSemanticState(
                    metadataSource: metadataSource,
                    historyStatus: historyStatus,
                    latestFatigue: reconstructedSeries.latestFatigue,
                    latestCapacity: latestCapacity
                ),
                latestLoad: latestLoad,
                latestCapacity: latestCapacity
            ),
            latestCacheUpdatedAt: cached.map(\.updatedAt).max()
        )
    }

    private func resolvedHistoryStatus(
        from cached: [CachedTrainingLoadPoint],
        metadataSource: CachedTrainingLoadPoint
    ) -> TrainingLoadHistoryStatus {
        if let rawValue = metadataSource.historyStatusRaw,
           let status = TrainingLoadHistoryStatus(rawValue: rawValue) {
            return status
        }

        return derivedHistoryStatus(from: cached)
    }

    private func derivedHistoryStatus(from cached: [CachedTrainingLoadPoint]) -> TrainingLoadHistoryStatus {
        guard let firstDate = cached.first?.date, let lastDate = cached.last?.date else {
            return .missing
        }

        let firstDay = calendar.startOfDay(for: firstDate)
        let lastDay = calendar.startOfDay(for: lastDate)
        let coverageDays = max(
            (calendar.dateComponents([.day], from: firstDay, to: lastDay).day ?? (cached.count - 1)) + 1,
            cached.count
        )

        switch coverageDays {
        case 42...:
            return .available
        case 14...41:
            return .partial
        case 1...13:
            return .insufficientHistory
        default:
            return .missing
        }
    }

    private func reconstructedSeries(
        from cached: [CachedTrainingLoadPoint],
        sliced: [CachedTrainingLoadPoint]
    ) -> ReconstructedTrainingLoadSeries {
        let persistedCapacitySeries = cached.map(\.capacity)
        let shouldReconstructCapacity = persistedCapacitySeries.contains(where: { $0 == nil })

        let capacitySeries: [Double]
        if shouldReconstructCapacity {
            capacitySeries = calculateEMASeries(
                cached.map(\.trimp),
                windowDays: Self.fitnessWindowDays
            )
        } else {
            capacitySeries = persistedCapacitySeries.map { $0 ?? 0 }
        }

        let fatigueSeries = calculateEMASeries(
            cached.map(\.trimp),
            windowDays: Self.fatigueWindowDays
        )

        let capacityByDate = Dictionary(
            uniqueKeysWithValues: zip(cached.map(\.date), capacitySeries)
        )
        let items = sliced.map { item in
            TrainingLoadItemDTO(
                date: item.date,
                load: item.trimp,
                capacity: capacityByDate[item.date] ?? 0,
                trimp: item.trimp
            )
        }

        return ReconstructedTrainingLoadSeries(
            items: items,
            latestCapacity: capacitySeries.last ?? 0,
            latestFatigue: fatigueSeries.last ?? 0
        )
    }

    private func resolvedSemanticState(
        metadataSource: CachedTrainingLoadPoint,
        historyStatus: TrainingLoadHistoryStatus,
        latestFatigue: Double,
        latestCapacity: Double
    ) -> TrainingLoadSemanticState? {
        if let rawValue = metadataSource.semanticStateRaw,
           let semanticState = TrainingLoadSemanticState(rawValue: rawValue) {
            return semanticState
        }

        guard historyStatus != .missing, historyStatus != .insufficientHistory, latestCapacity > 0 else {
            return nil
        }

        let ratio = latestFatigue / latestCapacity
        if ratio < Self.loadCapacityThresholds.belowCapacityUpperBound {
            return .belowCapacity
        }
        if ratio <= Self.loadCapacityThresholds.withinRangeUpperBound {
            return .withinRange
        }
        if ratio <= Self.loadCapacityThresholds.nearLimitUpperBound {
            return .nearLimit
        }
        return .aboveCapacity
    }

    private func calculateEMASeries(_ values: [Double], windowDays: Int) -> [Double] {
        guard !values.isEmpty else {
            return []
        }

        let alpha = 2 / (Double(windowDays) + 1)
        var series: [Double] = []
        var currentEMA = 0.0

        for value in values {
            currentEMA = currentEMA + alpha * (value - currentEMA)
            series.append(currentEMA)
        }

        return series
    }

    // Pragmatic namespace isolation without widening SwiftData model scope in Phase 4.1.
    private func scopedSportKey(for sport: TrainingLoadSportFilter) -> String {
        "\(cacheScope)|\(sport.rawValue)"
    }

    #if DEBUG
    private func debugEmit(_ message: String) {
        logger.log("\(message, privacy: .public)")
        print("[TrainingLoadRepository] \(message)")
    }

    private func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        return isoFormatter.string(from: date)
    }
    #endif
}

private struct TrainingLoadNetworkContextError: LocalizedError {
    let underlying: Error
    let baseURL: URL
    let sport: TrainingLoadSportFilter

    var errorDescription: String? {
        "\(underlying.localizedDescription) [baseURL=\(baseURL.absoluteString) sport=\(sport.rawValue)]"
    }
}

enum TrainingLoadDataSource: String, Equatable, Sendable {
    case remote
    case cache
}

struct TrainingLoadFreshness: Equatable, Sendable {
    let source: TrainingLoadDataSource
    let baseURL: URL
    let remoteAttempted: Bool
    let remoteFailureDescription: String?
    let fetchedAt: Date
    let latestPointDate: Date?
    let cacheUpdatedAt: Date?
}

struct TrainingLoadFetchResult: Equatable, Sendable {
    let summary: TrainingLoadSummaryDTO
    let freshness: TrainingLoadFreshness
}
