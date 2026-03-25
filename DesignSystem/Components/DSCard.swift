import SwiftUI

enum DSCardStyle {
    case flat
    case standard
    case muted
    case floating
}

struct DSCard<Content: View>: View {
    typealias Style = DSCardStyle

    private let style: Style
    private let minHeight: CGFloat?
    private let content: Content

    init(style: Style = .standard, minHeight: CGFloat? = nil, @ViewBuilder content: () -> Content) {
        self.style = style
        self.minHeight = minHeight
        self.content = content()
    }

    private var elevation: AppElevation {
        switch style {
        case .flat:
            .flat
        case .standard:
            .card
        case .muted:
            .dropdown
        case .floating:
            .modal
        }
    }

    var body: some View {
        content
            .padding(AppSpacing.x16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .frame(minHeight: minHeight, alignment: .topLeading)
            .background(elevation.surfaceColor)
            .clipShape(RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous))
            .modifier(DSCardChrome(style: style, shadow: elevation.shadow))
    }
}

private struct DSCardChrome: ViewModifier {
    let style: DSCardStyle
    let shadow: AppShadow?

    func body(content: Content) -> some View {
        switch style {
        case .flat:
            content
        case .standard, .muted, .floating:
            content
                .overlay(
                    RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                        .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                )
                .appShadow(shadow)
        }
    }
}

struct DSMetricSnapshotCard: View {
    enum Density {
        case regular
        case compact
    }

    struct Item: Identifiable {
        enum Emphasis {
            case primary
            case subdued
        }

        let id = UUID()
        let title: String
        let value: String
        let detail: String?
        let emphasis: Emphasis
        let tint: Color

        init(
            title: String,
            value: String,
            detail: String? = nil,
            emphasis: Emphasis = .primary,
            tint: Color = AppColors.Text.primary
        ) {
            self.title = title
            self.value = value
            self.detail = detail
            self.emphasis = emphasis
            self.tint = tint
        }
    }

    private let eyebrow: String?
    private let items: [Item]
    private let footerText: String?
    private let accessory: AnyView?
    private let cardStyle: DSCardStyle
    private let density: Density
    private var isIntegrated: Bool {
        cardStyle == .flat
    }

    init(
        eyebrow: String? = nil,
        items: [Item],
        footerText: String? = nil,
        accessory: AnyView? = nil,
        style: DSCardStyle = .standard,
        density: Density = .regular
    ) {
        self.eyebrow = eyebrow
        self.items = items
        self.footerText = footerText
        self.accessory = accessory
        self.cardStyle = style
        self.density = density
    }

    var body: some View {
        DSCard(style: cardStyle) {
            VStack(alignment: .leading, spacing: cardSpacing) {
                if eyebrow != nil || accessory != nil {
                    HStack(alignment: .center, spacing: AppSpacing.x12) {
                        if let eyebrow {
                            Text(eyebrow)
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                        }

                        Spacer(minLength: AppSpacing.x8)

                        if let accessory {
                            accessory
                        }
                    }
                }

                metricTiles

                if let footerText, !isIntegrated {
                    Text(footerText)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }
        }
    }

    private var cardSpacing: CGFloat {
        if isIntegrated && density == .compact {
            return AppSpacing.x4
        }
        return isIntegrated ? AppSpacing.x8 : AppSpacing.x12
    }

    @ViewBuilder
    private var metricTiles: some View {
        if isIntegrated {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: density == .compact ? AppSpacing.x8 : AppSpacing.x12) {
                    ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                        DSMetricSnapshotTile(item: item, embedded: true, density: density)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        if index < items.count - 1 {
                            Rectangle()
                                .fill(AppColors.Stroke.subtle.opacity(0.65))
                                .frame(width: 1, height: density == .compact ? AppSpacing.x40 : AppSpacing.x48 + AppSpacing.x12)
                        }
                    }
                }

                VStack(alignment: .leading, spacing: density == .compact ? 2 : AppSpacing.x4) {
                    ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                        DSMetricSnapshotTile(item: item, embedded: true, density: density)

                        if index < items.count - 1 {
                            Rectangle()
                                .fill(AppColors.Stroke.subtle.opacity(0.65))
                                .frame(height: 1)
                        }
                    }
                }
            }
        } else {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: AppSpacing.x12) {
                    ForEach(items) { item in
                        DSMetricSnapshotTile(item: item, embedded: false, density: density)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    ForEach(items) { item in
                        DSMetricSnapshotTile(item: item, embedded: false, density: density)
                    }
                }
            }
        }
    }
}

struct DSExplainabilityCard: View {
    enum Layout {
        case standard
        case compactColumns
    }

    struct Item: Identifiable {
        enum Emphasis: Equatable {
            case primary
            case secondary
        }

        enum Status: Equatable {
            case measured
            case estimated
            case proxy
            case missing
        }

        let id = UUID()
        let title: String
        let value: String
        let unit: String?
        let baselineHint: String?
        let reason: String
        let status: Status
        let emphasis: Emphasis
        let tint: Color

        init(
            title: String,
            value: String,
            unit: String? = nil,
            baselineHint: String? = nil,
            reason: String,
            status: Status = .measured,
            emphasis: Emphasis = .primary,
            tint: Color = AppColors.Text.primary
        ) {
            self.title = title
            self.value = value
            self.unit = unit
            self.baselineHint = baselineHint
            self.reason = reason
            self.status = status
            self.emphasis = emphasis
            self.tint = tint
        }
    }

    private let eyebrow: String?
    private let primaryItems: [Item]
    private let secondaryItems: [Item]
    private let footerText: String?
    private let cardStyle: DSCardStyle
    private let layout: Layout
    private var isIntegrated: Bool {
        cardStyle == .flat
    }
    private var usesCompactColumns: Bool {
        isIntegrated && layout == .compactColumns
    }

    init(
        eyebrow: String? = nil,
        primaryItems: [Item],
        secondaryItems: [Item] = [],
        footerText: String? = nil,
        style: DSCardStyle = .standard,
        layout: Layout = .standard
    ) {
        self.eyebrow = eyebrow
        self.primaryItems = primaryItems
        self.secondaryItems = secondaryItems
        self.footerText = footerText
        self.cardStyle = style
        self.layout = layout
    }

    var body: some View {
        DSCard(style: cardStyle) {
            VStack(alignment: .leading, spacing: usesCompactColumns ? AppSpacing.x8 : AppSpacing.x12) {
                if let eyebrow {
                    Text(eyebrow)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }

                primaryContent

                if !secondaryItems.isEmpty {
                    secondaryContent
                }

                if let footerText, !usesCompactColumns {
                    Text(footerText)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }
        }
    }

    @ViewBuilder
    private var primaryContent: some View {
        if usesCompactColumns {
            HStack(alignment: .top, spacing: AppSpacing.x8) {
                ForEach(Array(primaryItems.enumerated()), id: \.element.id) { index, item in
                    DSExplainabilityCompactTile(item: item)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    if index < primaryItems.count - 1 {
                        Rectangle()
                            .fill(AppColors.Stroke.subtle.opacity(0.65))
                            .frame(width: 1, height: AppSpacing.x64)
                    }
                }
            }
        } else {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: AppSpacing.x12) {
                    ForEach(primaryItems) { item in
                        DSExplainabilityTile(item: item, embedded: isIntegrated)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    ForEach(primaryItems) { item in
                        DSExplainabilityTile(item: item, embedded: isIntegrated)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var secondaryContent: some View {
        if usesCompactColumns {
            VStack(alignment: .leading, spacing: AppSpacing.x4 + 2) {
                Rectangle()
                    .fill(AppColors.Stroke.subtle.opacity(0.65))
                    .frame(height: 1)

                Text("Context")
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)

                VStack(alignment: .leading, spacing: AppSpacing.x4) {
                    ForEach(secondaryItems) { item in
                        DSExplainabilityContextRow(item: item)
                    }
                }
            }
        } else {
            VStack(alignment: .leading, spacing: AppSpacing.x8) {
                Text("Context")
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)

                VStack(alignment: .leading, spacing: AppSpacing.x8) {
                    ForEach(secondaryItems) { item in
                        DSExplainabilityTile(item: item, embedded: isIntegrated)
                    }
                }
            }
        }
    }
}

private struct DSMetricSnapshotTile: View {
    let item: DSMetricSnapshotCard.Item
    let embedded: Bool
    let density: DSMetricSnapshotCard.Density

    var body: some View {
        VStack(alignment: .leading, spacing: tileSpacing) {
            Text(item.title)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)

            Text(item.value)
                .appTextStyle(item.emphasis == .primary ? AppTypography.headingH2 : AppTypography.headingH3)
                .foregroundStyle(item.tint)
                .monospacedDigit()

            if let detail {
                Text(detail)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .lineLimit(compactEmbedded ? 1 : nil)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(tilePadding)
        .frame(minHeight: tileMinHeight, alignment: .leading)
        .background(embedded ? Color.clear : AppColors.Surface.cardMuted)
        .clipShape(RoundedRectangle(cornerRadius: embedded ? AppRadius.small : AppRadius.medium, style: .continuous))
        .overlay(
            Group {
                if !embedded {
                    RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                        .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                }
            }
        )
    }

    private var detail: String? {
        item.detail
    }

    private var compactEmbedded: Bool {
        embedded && density == .compact
    }

    private var tileSpacing: CGFloat {
        compactEmbedded ? AppSpacing.x4 : AppSpacing.x8
    }

    private var tilePadding: CGFloat {
        if compactEmbedded {
            return 2
        }
        return embedded ? AppSpacing.x4 : AppSpacing.x12
    }

    private var tileMinHeight: CGFloat {
        if compactEmbedded {
            return AppSpacing.x40
        }
        return embedded ? AppSpacing.x40 + AppSpacing.x8 : AppSpacing.x64 + AppSpacing.x12
    }
}

private struct DSExplainabilityTile: View {
    let item: DSExplainabilityCard.Item
    let embedded: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            HStack(alignment: .top, spacing: AppSpacing.x8) {
                Text(item.title)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)

                Spacer(minLength: AppSpacing.x8)

                if let statusTitle {
                    DSMetricPill(
                        statusTitle,
                        iconSystemName: statusIcon,
                        variant: statusVariant
                    )
                }
            }

            HStack(alignment: .firstTextBaseline, spacing: AppSpacing.x4) {
                Text(item.value)
                    .appTextStyle(item.emphasis == .primary ? AppTypography.headingH2 : AppTypography.headingH3)
                    .foregroundStyle(valueColor)
                    .monospacedDigit()

                if let unit = item.unit, !unit.isEmpty {
                    Text(unit)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }

            if let baselineHint {
                Text(baselineHint)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            Text(item.reason)
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .lineLimit(embedded ? 1 : nil)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(embedded ? AppSpacing.x4 : AppSpacing.x12)
        .background(backgroundColor)
        .clipShape(RoundedRectangle(cornerRadius: embedded ? AppRadius.small : AppRadius.medium, style: .continuous))
        .overlay(
            Group {
                if !embedded {
                    RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                        .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                }
            }
        )
    }

    private var baselineHint: String? {
        guard item.status == .measured else { return nil }
        return item.baselineHint
    }

    private var backgroundColor: Color {
        guard !embedded else { return Color.clear }
        return item.emphasis == .primary ? AppColors.Surface.cardMuted : AppColors.Background.elevated
    }

    private var valueColor: Color {
        switch item.status {
        case .measured:
            return item.tint
        case .estimated, .proxy, .missing:
            return AppColors.Text.secondary
        }
    }

    private var statusTitle: String? {
        switch item.status {
        case .measured:
            return nil
        case .estimated:
            return "Estimated"
        case .proxy:
            return "Proxy"
        case .missing:
            return "Missing"
        }
    }

    private var statusIcon: String? {
        switch item.status {
        case .measured:
            return nil
        case .estimated:
            return "chart.bar.xaxis"
        case .proxy:
            return "sparkles"
        case .missing:
            return "minus.circle"
        }
    }

    private var statusVariant: DSMetricPill.Variant {
        switch item.status {
        case .measured:
            return .neutral
        case .estimated:
            return .info
        case .proxy:
            return .neutral
        case .missing:
            return .warning
        }
    }
}

private struct DSExplainabilityCompactTile: View {
    let item: DSExplainabilityCard.Item

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x4) {
            Text(item.title)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)
                .lineLimit(1)

            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(item.value)
                    .appTextStyle(AppTypography.heading4)
                    .foregroundStyle(valueColor)
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)

                if let unit = item.unit, !unit.isEmpty {
                    Text(unit)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                        .lineLimit(1)
                }
            }

            if let baselineHint {
                Text(baselineHint)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.9)
                    .truncationMode(.tail)
            }

            Text(reasonText)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(reasonColor)
                .lineLimit(1)
                .minimumScaleFactor(0.9)
                .truncationMode(.tail)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(minHeight: AppSpacing.x48 + AppSpacing.x8, alignment: .topLeading)
        .accessibilityElement(children: .combine)
    }

    private var baselineHint: String? {
        item.baselineHint
    }

    private var reasonText: String {
        switch item.status {
        case .measured:
            return compactMeasuredReason(item.reason)
        case .estimated:
            return "Estimated"
        case .proxy:
            return "Proxy"
        case .missing:
            return "Missing"
        }
    }

    private func compactMeasuredReason(_ text: String) -> String {
        let lowercased = text.lowercased()

        if lowercased.contains("above usual") {
            return "Above usual"
        }
        if lowercased.contains("below usual") {
            return "Below usual"
        }
        if lowercased.contains("near baseline") {
            return "Near baseline"
        }
        if lowercased.contains("baseline") {
            return "At baseline"
        }
        if lowercased.contains("elevated") {
            return "Elevated"
        }
        if lowercased.contains("missing") {
            return "Missing"
        }

        return text
    }

    private var valueColor: Color {
        switch item.status {
        case .measured:
            return item.tint
        case .estimated, .proxy, .missing:
            return AppColors.Text.secondary
        }
    }

    private var reasonColor: Color {
        switch item.status {
        case .measured:
            return AppColors.Text.secondary
        case .estimated:
            return AppColors.Accent.blue
        case .proxy:
            return AppColors.Text.secondary
        case .missing:
            return AppColors.Accent.orange
        }
    }
}

private struct DSExplainabilityContextRow: View {
    let item: DSExplainabilityCard.Item

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.x8) {
            VStack(alignment: .leading, spacing: 1) {
                Text(item.title)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)

                HStack(alignment: .firstTextBaseline, spacing: 2) {
                    Text(item.value)
                        .appTextStyle(AppTypography.heading4)
                        .foregroundStyle(valueColor)
                        .monospacedDigit()

                    if let unit = item.unit, !unit.isEmpty {
                        Text(unit)
                            .appTextStyle(AppTypography.labelSmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    }
                }
            }

            Spacer(minLength: AppSpacing.x8)

            Text(contextDescriptor)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)
                .lineLimit(1)
                .minimumScaleFactor(0.9)
                .truncationMode(.tail)
        }
        .accessibilityElement(children: .combine)
    }

    private var valueColor: Color {
        switch item.status {
        case .measured:
            return item.tint
        case .estimated, .proxy, .missing:
            return AppColors.Text.secondary
        }
    }

    private var contextDescriptor: String {
        switch item.status {
        case .measured:
            return compactMeasuredContext(item.reason)
        case .estimated:
            return "Estimated"
        case .proxy:
            return "Proxy"
        case .missing:
            return "Missing"
        }
    }

    private func compactMeasuredContext(_ text: String) -> String {
        let lowercased = text.lowercased()

        if lowercased.contains("elevated") {
            return "Elevated"
        }
        if lowercased.contains("above") {
            return "Above usual"
        }
        if lowercased.contains("below") {
            return "Below usual"
        }
        if lowercased.contains("baseline") {
            return "At baseline"
        }

        return text
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        VStack(spacing: AppSpacing.x16) {
            DSCard {
                Text("Card")
                    .appTextStyle(AppTypography.headingH3)
                    .foregroundStyle(AppColors.Text.primary)
            }
            DSCard(style: .muted) {
                Text("Muted")
                    .appTextStyle(AppTypography.bodyRegular)
                    .foregroundStyle(AppColors.Text.secondary)
            }
            DSMetricSnapshotCard(
                eyebrow: "Load snapshot",
                items: [
                    .init(title: "7-Day Load", value: "175", detail: "Weekly total"),
                    .init(title: "Fitness", value: "35", detail: "Base form"),
                    .init(title: "Fatigue", value: "38", detail: "Recent strain")
                ],
                footerText: "History is still consolidating.",
                accessory: AnyView(
                    DSMetricPill("Partial history", iconSystemName: "chart.line.uptrend.xyaxis", variant: .info)
                )
            )
            DSExplainabilityCard(
                eyebrow: "Readiness drivers",
                primaryItems: [
                    .init(
                        title: "Sleep",
                        value: "7h 38m",
                        baselineHint: "Usual 7h 12m",
                        reason: "Sleep ran above usual.",
                        tint: AppColors.Accent.green
                    ),
                    .init(
                        title: "HRV",
                        value: "61",
                        unit: "ms",
                        baselineHint: "Usual 56 ms",
                        reason: "HRV rose above usual.",
                        tint: AppColors.Accent.green
                    ),
                    .init(
                        title: "RHR",
                        value: "49",
                        unit: "bpm",
                        baselineHint: "Usual 52 bpm",
                        reason: "RHR stayed below usual.",
                        tint: AppColors.Accent.green
                    )
                ],
                secondaryItems: [
                    .init(
                        title: "Exertion",
                        value: "182",
                        unit: "load",
                        reason: "Exertion stayed elevated.",
                        status: .estimated,
                        emphasis: .secondary,
                        tint: AppColors.Accent.orange
                    )
                ],
                footerText: "Sleep, HRV, and RHR drive the score. Exertion stays contextual.",
                style: .flat,
                layout: .compactColumns
            )
        }
        .padding(AppSpacing.x24)
    }
}
