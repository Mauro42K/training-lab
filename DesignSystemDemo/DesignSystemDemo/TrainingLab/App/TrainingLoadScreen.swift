import SwiftUI

struct TrainingLoadScreen: View {
    let environment: AppEnvironment

    @State private var selectedFilter: TrainingLoadSportFilter = .all
    @State private var trendSnapshot = TrainingLoadFetchResult.empty(baseURL: URL(string: "https://api.training-lab.mauro42k.com")!)
    @State private var selectedDay: SelectedTrainingLoadDay?
    @State private var dayWorkouts: [WorkoutDTO] = []
    @State private var isLoading = false
    @State private var isLoadingDay = false
    @State private var hasLoadedOnce = false
    @State private var errorMessage: String?

    private let calendar = Calendar.current

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                DSSectionHeader(title: "Load Trend", actionLabel: {
                    Text("Last 28 days")
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                })

                TrainingLoadSummaryRow(
                    today: todayTotal,
                    sevenDays: sevenDayTotal,
                    twentyEightDays: twentyEightDayTotal
                )

                TrainingLoadFilterControl(selection: $selectedFilter)

                if isLoading && !hasLoadedOnce {
                    DSLoadingState()
                } else {
                    if let freshnessMessage {
                        TrendFreshnessCard(
                            message: freshnessMessage,
                            source: trendSnapshot.freshness.source
                        )
                    }

                    if shouldShowDiagnostics {
                        TrendDiagnosticsRow(freshness: trendSnapshot.freshness)
                    }

                    TrainingLoadTrendCard(
                        summary: trendSummary,
                        points: chartPoints,
                        onSelectDay: { day in
                            Task { await selectDay(day) }
                        }
                    )
                    .opacity(isLoading ? 0.72 : 1)
                    .animation(.easeInOut(duration: 0.2), value: isLoading)
                }

                if let errorMessage {
                    DSCard(style: .muted) {
                        HStack(spacing: AppSpacing.x8) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(AppColors.Accent.orange)
                            Text(errorMessage)
                                .appTextStyle(AppTypography.bodySmall)
                                .foregroundStyle(AppColors.Text.secondary)
                        }
                    }
                }
            }
            .padding(AppSpacing.x16)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .navigationTitle("Training Load")
        .task(id: selectedFilter) {
            await loadSeries()
        }
        .sheet(item: $selectedDay, onDismiss: clearSelectedDaySelection) { selection in
            TrainingLoadDayDetailSheet(
                day: selection.date,
                workouts: dayWorkouts,
                isLoading: isLoadingDay
            )
        }
    }

    private var sortedPoints: [TrainingLoadItemDTO] {
        trendSummary.items.sorted { $0.date < $1.date }
    }

    private var chartPoints: [TrainingLoadChartPoint] {
        sortedPoints.map { item in
            TrainingLoadChartPoint(
                id: item.date,
                date: item.date,
                load: item.load,
                capacity: item.capacity,
                isToday: calendar.isDateInToday(item.date),
                isSelected: selectedDay.map { calendar.isDate($0.date, inSameDayAs: item.date) } ?? false
            )
        }
    }

    private var todayTotal: Double {
        trailingCalendarWindowTotal(days: 1)
    }

    private var sevenDayTotal: Double {
        trailingCalendarWindowTotal(days: 7)
    }

    private var twentyEightDayTotal: Double {
        trailingCalendarWindowTotal(days: 28)
    }

    private func loadSeries() async {
        isLoading = true
        defer { isLoading = false }

        do {
            trendSnapshot = try await environment.trainingLoadRepository.getTrainingLoad(
                days: 28,
                sport: selectedFilter
            )
            hasLoadedOnce = true
            errorMessage = nil
        } catch {
            trendSnapshot = .empty(baseURL: environment.apiBaseURL)
            hasLoadedOnce = true
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func selectDay(_ day: Date) async {
        selectedDay = SelectedTrainingLoadDay(date: day)
        isLoadingDay = true
        defer { isLoadingDay = false }

        do {
            let start = calendar.startOfDay(for: day)
            let end = calendar.date(byAdding: .day, value: 1, to: start)?.addingTimeInterval(-1) ?? start
            let workouts = try await environment.workoutsRepository.getWorkouts(
                from: start,
                to: end,
                sport: selectedFilter.sportType
            )
            if selectedDay.map({ calendar.isDate($0.date, inSameDayAs: day) }) == true {
                dayWorkouts = workouts
            }
        } catch {
            if selectedDay.map({ calendar.isDate($0.date, inSameDayAs: day) }) == true {
                dayWorkouts = []
            }
        }
    }

    private func clearSelectedDaySelection() {
        selectedDay = nil
        dayWorkouts = []
    }

    private var trendSummary: TrainingLoadSummaryDTO {
        trendSnapshot.summary
    }

    private var shouldShowDiagnostics: Bool {
        environment.runtimeEnvironment != .production
    }

    private var freshnessMessage: String? {
        guard let latestPointDate = trendSnapshot.freshness.latestPointDate,
              !calendar.isDateInToday(latestPointDate) else {
            return nil
        }

        let formattedDate = Self.longDateFormatter.string(from: latestPointDate)
        switch trendSnapshot.freshness.source {
        case .remote:
            return "Latest load data is through \(formattedDate)."
        case .cache:
            return "Showing cached load through \(formattedDate) while refresh is unavailable."
        }
    }

    private func trailingCalendarWindowTotal(days: Int) -> Double {
        guard days > 0 else { return 0 }

        let today = calendar.startOfDay(for: Date())
        let windowStart = calendar.date(byAdding: .day, value: -(days - 1), to: today) ?? today

        return sortedPoints.reduce(0) { partial, item in
            let itemDay = calendar.startOfDay(for: item.date)
            guard itemDay >= windowStart && itemDay <= today else {
                return partial
            }
            return partial + item.load
        }
    }

    private static let longDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "MMM d"
        return formatter
    }()
}

private struct SelectedTrainingLoadDay: Identifiable, Equatable {
    let date: Date

    var id: Date { date }
}

private extension TrainingLoadSportFilter {
    var sportType: SportType? {
        switch self {
        case .all:
            return nil
        case .run:
            return .run
        case .bike:
            return .bike
        case .strength:
            return .strength
        case .walk:
            return .walk
        }
    }
}

private struct TrendFreshnessCard: View {
    let message: String
    let source: TrainingLoadDataSource

    var body: some View {
        DSCard(style: .muted) {
            HStack(alignment: .top, spacing: AppSpacing.x8) {
                Image(systemName: source == .cache ? "clock.badge.exclamationmark" : "clock.arrow.circlepath")
                    .foregroundStyle(AppColors.Accent.orange)
                Text(message)
                    .appTextStyle(AppTypography.bodySmall)
                    .foregroundStyle(AppColors.Text.secondary)
            }
        }
    }
}

private struct TrendDiagnosticsRow: View {
    let freshness: TrainingLoadFreshness

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x4) {
            Text(
                "Source \(freshness.source.rawValue.uppercased()) | Base \(freshness.baseURL.absoluteString)"
            )
            Text(
                "Latest point \(Self.debugDateString(freshness.latestPointDate)) | Cache updated \(Self.debugDateString(freshness.cacheUpdatedAt))"
            )
            if let remoteFailureDescription = freshness.remoteFailureDescription {
                Text("Remote refresh failed: \(remoteFailureDescription)")
            } else {
                Text("Remote refresh succeeded")
            }
        }
        .appTextStyle(AppTypography.labelSmall)
        .foregroundStyle(AppColors.Text.secondary)
    }

    private static func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        return formatter.string(from: date)
    }

    private static let formatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter
    }()
}

private extension TrainingLoadFetchResult {
    static func empty(baseURL: URL) -> TrainingLoadFetchResult {
        TrainingLoadFetchResult(
            summary: TrainingLoadSummaryDTO(
                items: [],
                historyStatus: .missing,
                semanticState: nil,
                latestLoad: 0,
                latestCapacity: 0
            ),
            freshness: TrainingLoadFreshness(
                source: .cache,
                baseURL: baseURL,
                remoteAttempted: false,
                remoteFailureDescription: nil,
                fetchedAt: Date(),
                latestPointDate: nil,
                cacheUpdatedAt: nil
            )
        )
    }
}
