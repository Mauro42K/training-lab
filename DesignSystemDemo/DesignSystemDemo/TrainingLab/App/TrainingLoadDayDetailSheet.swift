import SwiftUI

struct TrainingLoadDayDetailSheet: View {
    let day: Date
    let workouts: [WorkoutDTO]
    let isLoading: Bool

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: AppSpacing.x12) {
                if !isLoading {
                    Text(summaryLine)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                        .padding(.horizontal, AppSpacing.x16)
                }

                if isLoading {
                    DSLoadingState()
                } else if workouts.isEmpty {
                    DSEmptyState(
                        iconSystemName: "chart.bar.xaxis",
                        title: "No workouts",
                        message: "No sessions found for this day and filter."
                    )
                } else {
                    workoutsList
                }
            }
            .background(AppColors.Background.primary.ignoresSafeArea())
            .navigationTitle(Self.dayFormatter.string(from: day))
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
        }
    }

    private var workoutsList: some View {
        let list = List(workouts, id: \.uuid) { workout in
            VStack(alignment: .leading, spacing: AppSpacing.x4) {
                Text(workout.sport.rawValue.capitalized)
                    .appTextStyle(AppTypography.headingH3)
                    .foregroundStyle(AppColors.Text.primary)
                Text(Self.timeFormatter.string(from: workout.start))
                    .appTextStyle(AppTypography.bodySmall)
                    .foregroundStyle(AppColors.Text.secondary)
                Text("Duration \(Self.durationString(workout.durationSec))")
                    .appTextStyle(AppTypography.bodySmall)
                    .foregroundStyle(AppColors.Text.secondary)
            }
            .padding(.vertical, AppSpacing.x4)
            .listRowBackground(AppColors.Surface.cardMuted)
        }

        #if os(iOS)
        return AnyView(
            list
                .listStyle(.insetGrouped)
                .scrollContentBackground(.hidden)
                .background(AppColors.Background.primary)
        )
        #else
        return AnyView(
            list
                .listStyle(.inset)
                .background(AppColors.Background.primary)
        )
        #endif
    }

    private var summaryLine: String {
        switch workouts.count {
        case 0:
            return "No sessions"
        case 1:
            return "1 session"
        default:
            return "\(workouts.count) sessions"
        }
    }

    private static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }()

    private static let dayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }()

    private static func durationString(_ totalSeconds: Int) -> String {
        let hours = totalSeconds / 3600
        let minutes = (totalSeconds % 3600) / 60
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        }
        return "\(minutes)m"
    }
}
