import SwiftUI

struct TrainingLoadChartCard: View {
    let points: [TrainingLoadItemDTO]
    @Binding var selectedDay: Date?
    let onSelectDay: (Date) -> Void

    var body: some View {
        DSChartCard(
            title: "Daily TRIMP",
            subtitle: "28-day load"
        ) {
            TrainingLoadChartView(
                points: points,
                selectedDay: $selectedDay,
                onSelectDay: onSelectDay
            )
        }
    }
}

struct TrainingLoadChartView: View {
    let points: [TrainingLoadItemDTO]
    @Binding var selectedDay: Date?
    let onSelectDay: (Date) -> Void

    private let calendar = Calendar.current

    var body: some View {
        GeometryReader { proxy in
            let maxValue = max(points.map(\.trimp).max() ?? 0, 1)

            HStack(alignment: .bottom, spacing: AppSpacing.x4) {
                ForEach(points) { point in
                    RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                        .fill(color(for: point.date))
                        .frame(
                            maxWidth: .infinity,
                            minHeight: 4,
                            maxHeight: max(
                                4,
                                CGFloat(point.trimp / maxValue) * proxy.size.height
                            )
                        )
                        .onTapGesture {
                            selectedDay = point.date
                            onSelectDay(point.date)
                        }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
        }
        .frame(minHeight: 180)
    }

    private func color(for day: Date) -> Color {
        if let selectedDay, calendar.isDate(day, inSameDayAs: selectedDay) {
            return AppColors.Accent.orange
        }
        if calendar.isDateInToday(day) {
            return AppColors.Accent.blue
        }
        return AppColors.Stroke.strong
    }
}
