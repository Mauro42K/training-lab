import SwiftUI

struct TrainingLoadDayDetailSheet: View {
    let day: Date
    let workouts: [WorkoutDTO]
    let isLoading: Bool

    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    DSLoadingState()
                } else if workouts.isEmpty {
                    DSEmptyState(
                        iconSystemName: "chart.bar.xaxis",
                        title: "No workouts",
                        message: "No sessions found for this day and filter."
                    )
                } else {
                    List(workouts, id: \.uuid) { workout in
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
                        .listRowBackground(AppColors.Background.elevated)
                    }
                    .scrollContentBackground(.hidden)
                    .background(AppColors.Background.primary)
                }
            }
            .padding(AppSpacing.x16)
            .background(AppColors.Background.primary.ignoresSafeArea())
            .navigationTitle(Self.dayFormatter.string(from: day))
            .navigationBarTitleDisplayMode(.inline)
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
