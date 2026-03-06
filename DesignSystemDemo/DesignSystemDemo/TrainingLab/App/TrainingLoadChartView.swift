import SwiftUI

struct TrainingLoadChartPoint: Identifiable, Equatable {
    let id: Date
    let date: Date
    let value: Double
    let isToday: Bool
    let isSelected: Bool
}

struct TrainingLoadChartCard: View {
    let points: [TrainingLoadChartPoint]
    let onSelectDay: (Date) -> Void

    var body: some View {
        DSChartCard(
            title: "Daily TRIMP",
            subtitle: "28-day load"
        ) {
            TrainingLoadChartView(
                points: points,
                onSelectDay: onSelectDay
            )
        }
    }
}

struct TrainingLoadChartView: View {
    let points: [TrainingLoadChartPoint]
    let onSelectDay: (Date) -> Void
    @State private var hoveredPointID: Date?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            GeometryReader { proxy in
                let maxValue = max(points.map(\.value).max() ?? 0, 1)

                HStack(alignment: .bottom, spacing: AppSpacing.x4) {
                    ForEach(points) { point in
                        let isHovered = hoveredPointID == point.id
                        RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                            .fill(color(for: point, isHovered: isHovered))
                            .overlay {
                                if isHovered && !point.isSelected {
                                    RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                        .stroke(
                                            AppColors.Text.primary.opacity(point.isToday ? 0.28 : 0.18),
                                            lineWidth: 1
                                        )
                                }
                            }
                            .scaleEffect(isHovered && !point.isSelected ? 1.02 : 1, anchor: .bottom)
                            .frame(
                                maxWidth: .infinity,
                                minHeight: 4,
                                maxHeight: max(
                                    4,
                                    CGFloat(point.value / maxValue) * proxy.size.height
                                )
                            )
                            .onHover { isHovering in
                                if isHovering {
                                    hoveredPointID = point.id
                                } else if hoveredPointID == point.id {
                                    hoveredPointID = nil
                                }
                            }
                            .onTapGesture {
                                onSelectDay(point.date)
                            }
                    }
                }
                .animation(.easeInOut(duration: 0.18), value: points)
                .animation(.easeInOut(duration: 0.14), value: hoveredPointID)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
            }
            .frame(minHeight: 170)

            TrainingLoadAxisLabels(points: points)
        }
    }

    private func color(for point: TrainingLoadChartPoint, isHovered: Bool) -> Color {
        if point.isSelected {
            return AppColors.Accent.orange
        }
        if point.isToday {
            return isHovered ? AppColors.Accent.blue.opacity(0.95) : AppColors.Accent.blue
        }
        if isHovered {
            return AppColors.Stroke.strong
        }
        return AppColors.Stroke.subtle
    }
}

private struct TrainingLoadAxisLabels: View {
    let points: [TrainingLoadChartPoint]

    var body: some View {
        Group {
            if points.count <= 7 {
                HStack(alignment: .center, spacing: AppSpacing.x4) {
                    ForEach(points) { point in
                        Text(Self.weekdayFormatter.string(from: point.date))
                            .appTextStyle(AppTypography.labelSmall)
                            .foregroundStyle(AppColors.Text.secondary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                            .frame(maxWidth: .infinity)
                    }
                }
            } else if points.count >= 28 {
                HStack(spacing: AppSpacing.x8) {
                    ForEach(anchorLabels, id: \.self) { label in
                        if label == "Today" {
                            Text(label)
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Accent.blue)
                                .lineLimit(1)
                                .minimumScaleFactor(0.9)
                        } else {
                            Text(label)
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                                .lineLimit(1)
                                .minimumScaleFactor(0.9)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            } else {
                HStack(alignment: .center, spacing: AppSpacing.x4) {
                    ForEach(Array(points.indices), id: \.self) { index in
                        if let label = labelsByIndex[index] {
                            Text(label)
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                                .lineLimit(1)
                                .minimumScaleFactor(0.8)
                                .frame(maxWidth: .infinity)
                        } else {
                            Color.clear
                                .frame(maxWidth: .infinity, minHeight: AppSpacing.x12)
                        }
                    }
                }
            }
        }
    }

    private var anchorLabels: [String] {
        ["28d", "21d", "14d", "7d", "Today"]
    }

    private var labelsByIndex: [Int: String] {
        guard !points.isEmpty else {
            return [:]
        }

        let strideValue = max(1, points.count / 5)
        var labels: [Int: String] = [:]
        for index in stride(from: 0, to: points.count, by: strideValue) {
            if index < points.count {
                labels[index] = Self.dayFormatter.string(from: points[index].date)
            }
        }
        labels[points.count - 1] = "Today"
        return labels
    }

    private static let weekdayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "EEE"
        return formatter
    }()

    private static let dayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "d"
        return formatter
    }()
}

#Preview {
    let calendar = Calendar.current
    let today = calendar.startOfDay(for: Date())
    let points = (0..<28).map { offset -> TrainingLoadChartPoint in
        let date = calendar.date(byAdding: .day, value: -(27 - offset), to: today) ?? today
        return TrainingLoadChartPoint(
            id: date,
            date: date,
            value: Double((offset % 7) * 12 + 8),
            isToday: calendar.isDateInToday(date),
            isSelected: offset == 21
        )
    }

    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        TrainingLoadChartCard(points: points) { _ in }
            .padding()
    }
}
