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
    private let minimumZeroHeight: CGFloat = 4
    private let minimumPositiveHeight: CGFloat = 7
    private let showSecondaryGuide = false

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            GeometryReader { proxy in
                let maxValue = max(points.map(\.value).max() ?? 0, 1)
                let hoveredPoint = points.first(where: { $0.id == hoveredPointID })
                let hoveredIndex = points.firstIndex(where: { $0.id == hoveredPointID })

                ZStack(alignment: .bottomLeading) {
                    if showSecondaryGuide {
                        Rectangle()
                            .fill(AppColors.Stroke.subtle.opacity(0.32))
                            .frame(height: 1)
                            .offset(y: -proxy.size.height * 0.45)
                    }

                    Rectangle()
                        .fill(AppColors.Stroke.subtle.opacity(0.65))
                        .frame(height: 1)

                    HStack(alignment: .bottom, spacing: AppSpacing.x4) {
                        ForEach(points) { point in
                            let isHovered = hoveredPointID == point.id
                            ZStack(alignment: .bottom) {
                                if isHovered && !point.isSelected {
                                    RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                        .fill(AppColors.Text.primary.opacity(0.07))
                                }

                                RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                    .fill(color(for: point, isHovered: isHovered))
                                    .overlay {
                                        if isHovered && !point.isSelected {
                                            RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                                .stroke(
                                                    AppColors.Text.primary.opacity(point.isToday ? 0.28 : 0.2),
                                                    lineWidth: 1
                                                )
                                        }
                                    }
                                    .scaleEffect(isHovered && !point.isSelected ? 1.02 : 1, anchor: .bottom)
                                    .frame(
                                        maxWidth: .infinity,
                                        minHeight: minimumZeroHeight,
                                        maxHeight: barHeight(for: point.value, maxValue: maxValue, chartHeight: proxy.size.height)
                                    )
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
                            .contentShape(Rectangle())
                            .animation(.easeInOut(duration: 0.14), value: isHovered)
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
                    .padding(.bottom, 1)

                    #if os(macOS)
                    if let hoveredPoint, let hoveredIndex {
                        HoverTooltip(point: hoveredPoint)
                            .position(
                                x: tooltipXPosition(for: hoveredIndex, count: points.count, width: proxy.size.width),
                                y: 14
                            )
                            .allowsHitTesting(false)
                    }
                    #endif
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
            return isHovered ? AppColors.Accent.blue : AppColors.Accent.blue.opacity(0.92)
        }
        if isHovered {
            return AppColors.Stroke.strong.opacity(0.96)
        }
        return AppColors.Stroke.subtle.opacity(0.9)
    }

    private func barHeight(for value: Double, maxValue: Double, chartHeight: CGFloat) -> CGFloat {
        let rawHeight = max(minimumZeroHeight, CGFloat(value / maxValue) * chartHeight)
        guard value > 0 else {
            return minimumZeroHeight
        }
        return max(rawHeight, minimumPositiveHeight)
    }

    private func tooltipXPosition(for index: Int, count: Int, width: CGFloat) -> CGFloat {
        guard count > 0 else {
            return width / 2
        }
        let columnWidth = width / CGFloat(count)
        let raw = (CGFloat(index) + 0.5) * columnWidth
        let inset: CGFloat = 62
        return min(max(raw, inset), max(inset, width - inset))
    }
}

private struct HoverTooltip: View {
    let point: TrainingLoadChartPoint

    var body: some View {
        HStack(spacing: AppSpacing.x4) {
            Text(Self.dateFormatter.string(from: point.date))
            Text("•")
                .foregroundStyle(AppColors.Text.secondary)
            Text("TRIMP \(Int(point.value.rounded()))")
        }
        .appTextStyle(AppTypography.labelSmall)
        .foregroundStyle(AppColors.Text.primary)
        .padding(.horizontal, AppSpacing.x8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                .fill(AppColors.Surface.cardMuted.opacity(0.96))
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                .stroke(AppColors.Stroke.subtle.opacity(0.75), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.22), radius: 3, x: 0, y: 1)
    }

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "MMM d"
        return formatter
    }()
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
                            .foregroundStyle(AppColors.Text.secondary.opacity(0.92))
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
                                .foregroundStyle(AppColors.Accent.blue.opacity(0.98))
                                .lineLimit(1)
                                .minimumScaleFactor(0.9)
                        } else {
                            Text(label)
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary.opacity(0.92))
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
                                .foregroundStyle(AppColors.Text.secondary.opacity(0.92))
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
