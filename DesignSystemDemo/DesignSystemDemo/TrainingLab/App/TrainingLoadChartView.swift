import SwiftUI

struct TrainingLoadChartPoint: Identifiable, Equatable {
    let id: Date
    let date: Date
    let load: Double
    let capacity: Double
    let isToday: Bool
    let isSelected: Bool
}

struct TrainingLoadTrendCard: View {
    let summary: TrainingLoadSummaryDTO
    let points: [TrainingLoadChartPoint]
    let onSelectDay: (Date) -> Void

    var body: some View {
        DSChartCard(
            title: "Load vs Capacity",
            subtitle: summary.cardSubtitle,
            style: .emphasized,
            legendItems: [
                .init(title: "Load", color: AppColors.Accent.blue.opacity(0.92)),
                .init(title: "Capacity", color: AppColors.Accent.orange),
            ]
        ) {
            VStack(alignment: .leading, spacing: AppSpacing.x12) {
                HStack(alignment: .top, spacing: AppSpacing.x12) {
                    VStack(alignment: .leading, spacing: AppSpacing.x4) {
                        Text(summary.headlineTitle)
                            .appTextStyle(AppTypography.headingH3)
                            .foregroundStyle(summary.headlineColor)

                        Text(summary.headlineDetail)
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    }

                    Spacer(minLength: AppSpacing.x12)

                    if summary.showsPrimaryMetrics {
                        HStack(spacing: AppSpacing.x12) {
                            TrendMetric(title: "Load", value: summary.latestLoad, color: AppColors.Accent.blue)
                            TrendMetric(title: "Capacity", value: summary.latestCapacity, color: AppColors.Accent.orange)
                        }
                    }
                }

                if summary.historyStatus == .missing {
                    TrendCardMissingState()
                } else {
                    TrainingLoadChartView(
                        points: points,
                        onSelectDay: onSelectDay
                    )
                }
            }
        }
    }
}

private struct TrendCardMissingState: View {
    var body: some View {
        VStack(spacing: AppSpacing.x12) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .appTextStyle(AppTypography.headingH2)
                .foregroundStyle(AppColors.Text.secondary)

            Text("No load history yet")
                .appTextStyle(AppTypography.headingH3)
                .foregroundStyle(AppColors.Text.primary)
                .multilineTextAlignment(.center)

            Text("Complete your first training sessions to start comparing load against capacity.")
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .frame(minHeight: 188)
        .padding(.horizontal, AppSpacing.x16)
        .padding(.vertical, AppSpacing.x12)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .fill(AppColors.Surface.cardMuted.opacity(0.36))
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .stroke(AppColors.Stroke.subtle.opacity(0.7), lineWidth: AppStrokeWidth.hairline)
        )
    }
}

struct TrainingLoadChartView: View {
    let points: [TrainingLoadChartPoint]
    let onSelectDay: (Date) -> Void
    @State private var hoveredPointID: Date?

    private let minimumZeroHeight: CGFloat = 4
    private let minimumPositiveHeight: CGFloat = 7

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            GeometryReader { proxy in
                let maxValue = chartMaxValue
                let hoveredPoint = points.first(where: { $0.id == hoveredPointID })
                let hoveredIndex = points.firstIndex(where: { $0.id == hoveredPointID })

                ZStack(alignment: .bottomLeading) {
                    Rectangle()
                        .fill(AppColors.Stroke.subtle.opacity(0.65))
                        .frame(height: 1)

                    capacityLine(in: proxy.size, maxValue: maxValue)

                    HStack(alignment: .bottom, spacing: AppSpacing.x4) {
                        ForEach(points) { point in
                            let isHovered = hoveredPointID == point.id
                            ZStack(alignment: .bottom) {
                                if isHovered && !point.isSelected {
                                    RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                        .fill(AppColors.Text.primary.opacity(0.07))
                                }

                                RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                    .fill(barColor(for: point, isHovered: isHovered))
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
                                        maxHeight: barHeight(
                                            for: point.load,
                                            maxValue: maxValue,
                                            chartHeight: proxy.size.height
                                        )
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

                    capacityMarkers(in: proxy.size, maxValue: maxValue)

                    #if os(macOS)
                    if let hoveredPoint, let hoveredIndex {
                        HoverTooltip(point: hoveredPoint)
                            .position(
                                x: tooltipXPosition(for: hoveredIndex, count: points.count, width: proxy.size.width),
                                y: 16
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

    private var chartMaxValue: Double {
        max(
            max(points.map(\.load).max() ?? 0, points.map(\.capacity).max() ?? 0),
            1
        )
    }

    @ViewBuilder
    private func capacityLine(in size: CGSize, maxValue: Double) -> some View {
        Path { path in
            guard !points.isEmpty else {
                return
            }

            for index in points.indices {
                let x = columnCenterX(for: index, count: points.count, width: size.width)
                let y = capacityYPosition(
                    for: points[index].capacity,
                    maxValue: maxValue,
                    chartHeight: size.height
                )

                if index == 0 {
                    path.move(to: CGPoint(x: x, y: y))
                } else {
                    path.addLine(to: CGPoint(x: x, y: y))
                }
            }
        }
        .stroke(
            AppColors.Accent.orange.opacity(0.96),
            style: StrokeStyle(lineWidth: 2.25, lineCap: .round, lineJoin: .round)
        )
    }

    @ViewBuilder
    private func capacityMarkers(in size: CGSize, maxValue: Double) -> some View {
        ForEach(Array(points.enumerated()), id: \.element.id) { index, point in
            if point.isToday || point.isSelected || hoveredPointID == point.id {
                Circle()
                    .fill(AppColors.Surface.card)
                    .overlay(
                        Circle()
                            .stroke(AppColors.Accent.orange, lineWidth: 2)
                    )
                    .frame(width: AppSpacing.x8, height: AppSpacing.x8)
                    .position(
                        x: columnCenterX(for: index, count: points.count, width: size.width),
                        y: capacityYPosition(
                            for: point.capacity,
                            maxValue: maxValue,
                            chartHeight: size.height
                        )
                    )
            }
        }
    }

    private func barColor(for point: TrainingLoadChartPoint, isHovered: Bool) -> Color {
        if point.isSelected {
            return AppColors.Accent.blue
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

    private func capacityYPosition(for value: Double, maxValue: Double, chartHeight: CGFloat) -> CGFloat {
        let normalized = max(0, min(value / maxValue, 1))
        return chartHeight - (CGFloat(normalized) * chartHeight)
    }

    private func columnCenterX(for index: Int, count: Int, width: CGFloat) -> CGFloat {
        guard count > 0 else {
            return width / 2
        }
        let columnWidth = width / CGFloat(count)
        return (CGFloat(index) + 0.5) * columnWidth
    }

    private func tooltipXPosition(for index: Int, count: Int, width: CGFloat) -> CGFloat {
        let raw = columnCenterX(for: index, count: count, width: width)
        let inset: CGFloat = 72
        return min(max(raw, inset), max(inset, width - inset))
    }
}

private struct TrendMetric: View {
    let title: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(alignment: .trailing, spacing: AppSpacing.x4) {
            Text(title)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)

            Text(String(Int(value.rounded())))
                .appTextStyle(AppTypography.headingH3)
                .foregroundStyle(color)
                .monospacedDigit()
        }
    }
}

private struct HoverTooltip: View {
    let point: TrainingLoadChartPoint

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(Self.dateFormatter.string(from: point.date))
                .foregroundStyle(AppColors.Text.primary)

            HStack(spacing: AppSpacing.x8) {
                tooltipLegend(color: AppColors.Accent.blue, label: "Load \(Int(point.load.rounded()))")
                tooltipLegend(color: AppColors.Accent.orange, label: "Cap \(Int(point.capacity.rounded()))")
            }
        }
        .appTextStyle(AppTypography.labelSmall)
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

    private func tooltipLegend(color: Color, label: String) -> some View {
        HStack(spacing: AppSpacing.x4) {
            Circle()
                .fill(color)
                .frame(width: 6, height: 6)
            Text(label)
                .foregroundStyle(AppColors.Text.secondary)
        }
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

    private struct AxisLabel: Identifiable {
        let id: Int
        let text: String
        let isToday: Bool
    }

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
                GeometryReader { proxy in
                    let width = proxy.size.width
                    let height = proxy.size.height

                    ZStack(alignment: .topLeading) {
                        ForEach(anchorLabels) { label in
                            axisLabel(label)
                                .position(
                                    x: clampedAxisXPosition(for: label, width: width),
                                    y: height / 2
                                )
                        }
                    }
                }
                .frame(height: AppSpacing.x16)
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

    private var anchorLabels: [AxisLabel] {
        guard hasTodayPoint else {
            let lastIndex = points.count - 1
            let anchorIndexes = [0, 7, 14, 21, lastIndex]
                .map { min($0, lastIndex) }
            return anchorIndexes.enumerated().map { offset, index in
                AxisLabel(
                    id: offset,
                    text: shortDateString(for: points[index].date),
                    isToday: points[index].isToday
                )
            }
        }

        return [
            AxisLabel(id: 0, text: "28d", isToday: false),
            AxisLabel(id: 1, text: "21d", isToday: false),
            AxisLabel(id: 2, text: "14d", isToday: false),
            AxisLabel(id: 3, text: "7d", isToday: false),
            AxisLabel(id: 4, text: "Today", isToday: true),
        ]
    }

    @ViewBuilder
    private func axisLabel(_ label: AxisLabel) -> some View {
        Text(label.text)
            .appTextStyle(AppTypography.labelSmall)
            .foregroundStyle(
                label.isToday
                    ? AppColors.Accent.blue.opacity(0.98)
                    : AppColors.Text.secondary.opacity(0.92)
            )
            .lineLimit(1)
            .minimumScaleFactor(0.85)
            .fixedSize(horizontal: true, vertical: false)
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
        labels[points.count - 1] = points[points.count - 1].isToday
            ? "Today"
            : shortDateString(for: points[points.count - 1].date)
        return labels
    }

    private var hasTodayPoint: Bool {
        points.contains(where: \.isToday)
    }

    private func shortDateString(for date: Date) -> String {
        Self.shortDateFormatter.string(from: date)
    }

    private func clampedAxisXPosition(for label: AxisLabel, width: CGFloat) -> CGFloat {
        guard !points.isEmpty else {
            return width / 2
        }

        let rawX = columnCenterX(for: label.id == 4 && hasTodayPoint ? points.count - 1 : axisIndex(for: label), count: points.count, width: width)
        let halfLabelWidth = estimatedHalfLabelWidth(for: label.text)
        return min(max(rawX, halfLabelWidth), max(halfLabelWidth, width - halfLabelWidth))
    }

    private func axisIndex(for label: AxisLabel) -> Int {
        switch label.id {
        case 0:
            return 0
        case 1:
            return min(7, points.count - 1)
        case 2:
            return min(14, points.count - 1)
        case 3:
            return min(21, points.count - 1)
        default:
            return points.count - 1
        }
    }

    private func columnCenterX(for index: Int, count: Int, width: CGFloat) -> CGFloat {
        guard count > 0 else {
            return width / 2
        }
        let columnWidth = width / CGFloat(count)
        return (CGFloat(index) + 0.5) * columnWidth
    }

    private func estimatedHalfLabelWidth(for text: String) -> CGFloat {
        let perCharacterWidth: CGFloat = 4.4
        return max(12, CGFloat(text.count) * perCharacterWidth)
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

    private static let shortDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "MMM d"
        return formatter
    }()
}

private extension TrainingLoadSummaryDTO {
    var showsPrimaryMetrics: Bool {
        switch historyStatus {
        case .available, .partial:
            return true
        case .insufficientHistory, .missing:
            return false
        }
    }

    var cardSubtitle: String {
        switch historyStatus {
        case .available:
            return "28-day comparative trend"
        case .partial:
            return "Trend still consolidating"
        case .insufficientHistory:
            return "Building a usable load baseline"
        case .missing:
            return "Waiting for the first load history"
        }
    }

    var headlineTitle: String {
        switch historyStatus {
        case .available, .partial:
            return semanticState?.displayTitle ?? "Tracking capacity"
        case .insufficientHistory:
            return "History still building"
        case .missing:
            return "No load history yet"
        }
    }

    var headlineDetail: String {
        switch historyStatus {
        case .available:
            return semanticState?.detailCopy ?? "Recent load is tracking your current capacity."
        case .partial:
            return semanticState?.partialDetailCopy ?? "Building the 42-day baseline."
        case .insufficientHistory:
            return "Need 14 days of load history before capacity becomes interpretable."
        case .missing:
            return "Complete your first training sessions to start comparing load against capacity."
        }
    }

    var headlineColor: Color {
        switch historyStatus {
        case .available:
            return semanticState?.accentColor ?? AppColors.Text.primary
        case .partial:
            return semanticState?.accentColor ?? AppColors.Accent.orange
        case .insufficientHistory:
            return AppColors.Accent.orange
        case .missing:
            return AppColors.Text.primary
        }
    }
}

private extension TrainingLoadSemanticState {
    var displayTitle: String {
        switch self {
        case .belowCapacity:
            return "Below capacity"
        case .withinRange:
            return "Within range"
        case .nearLimit:
            return "Near limit"
        case .aboveCapacity:
            return "Above capacity"
        }
    }

    var detailCopy: String {
        switch self {
        case .belowCapacity:
            return "Recent load is running below your current capacity."
        case .withinRange:
            return "Recent load is tracking your current capacity."
        case .nearLimit:
            return "Recent load is close to your current capacity ceiling."
        case .aboveCapacity:
            return "Recent load is running above your current capacity."
        }
    }

    var partialDetailCopy: String {
        switch self {
        case .belowCapacity:
            return "Below your current capacity. Baseline still building."
        case .withinRange:
            return "Tracking capacity. Baseline still building."
        case .nearLimit:
            return "Close to capacity. Baseline still building."
        case .aboveCapacity:
            return "Running above capacity. Baseline still building."
        }
    }

    var accentColor: Color {
        switch self {
        case .belowCapacity:
            return AppColors.Accent.blue
        case .withinRange:
            return AppColors.Accent.green
        case .nearLimit:
            return AppColors.Accent.orange
        case .aboveCapacity:
            return AppColors.Accent.red
        }
    }
}

#Preview {
    let calendar = Calendar.current
    let today = calendar.startOfDay(for: Date())
    let points = (0..<28).map { offset -> TrainingLoadChartPoint in
        let date = calendar.date(byAdding: .day, value: -(27 - offset), to: today) ?? today
        let load = Double((offset % 7) * 12 + 8)
        let capacity = Double(18 + offset)
        return TrainingLoadChartPoint(
            id: date,
            date: date,
            load: load,
            capacity: capacity,
            isToday: calendar.isDateInToday(date),
            isSelected: offset == 21
        )
    }

    let summary = TrainingLoadSummaryDTO(
        items: points.map { point in
            TrainingLoadItemDTO(
                date: point.date,
                load: point.load,
                capacity: point.capacity
            )
        },
        historyStatus: .available,
        semanticState: .withinRange,
        latestLoad: points.last?.load ?? 0,
        latestCapacity: points.last?.capacity ?? 0
    )

    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        TrainingLoadTrendCard(summary: summary, points: points) { _ in }
            .padding()
    }
}
