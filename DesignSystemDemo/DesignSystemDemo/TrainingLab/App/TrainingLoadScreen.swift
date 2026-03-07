import SwiftUI

struct TrainingLoadScreen: View {
    let environment: AppEnvironment

    @State private var selectedFilter: TrainingLoadSportFilter = .all
    @State private var points: [TrainingLoadItemDTO] = []
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
                    TrainingLoadChartCard(
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
        points.sorted { $0.date < $1.date }
    }

    private var chartPoints: [TrainingLoadChartPoint] {
        sortedPoints.map { item in
            TrainingLoadChartPoint(
                id: item.date,
                date: item.date,
                value: item.trimp,
                isToday: calendar.isDateInToday(item.date),
                isSelected: selectedDay.map { calendar.isDate($0.date, inSameDayAs: item.date) } ?? false
            )
        }
    }

    private var todayTotal: Double {
        let today = calendar.startOfDay(for: Date())
        return sortedPoints.first { calendar.isDate($0.date, inSameDayAs: today) }?.trimp ?? 0
    }

    private var sevenDayTotal: Double {
        sortedPoints.suffix(7).reduce(0) { $0 + $1.trimp }
    }

    private var twentyEightDayTotal: Double {
        sortedPoints.suffix(28).reduce(0) { $0 + $1.trimp }
    }

    private func loadSeries() async {
        isLoading = true
        defer { isLoading = false }

        do {
            points = try await environment.trainingLoadRepository.getTrainingLoad(
                days: 28,
                sport: selectedFilter
            )
            hasLoadedOnce = true
            errorMessage = nil
        } catch {
            points = []
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
