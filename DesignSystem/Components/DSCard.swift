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
    private var isIntegrated: Bool {
        cardStyle == .flat
    }

    init(
        eyebrow: String? = nil,
        items: [Item],
        footerText: String? = nil,
        accessory: AnyView? = nil,
        style: DSCardStyle = .standard
    ) {
        self.eyebrow = eyebrow
        self.items = items
        self.footerText = footerText
        self.accessory = accessory
        self.cardStyle = style
    }

    var body: some View {
        DSCard(style: cardStyle) {
            VStack(alignment: .leading, spacing: isIntegrated ? AppSpacing.x8 : AppSpacing.x12) {
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

    @ViewBuilder
    private var metricTiles: some View {
        if isIntegrated {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: AppSpacing.x12) {
                    ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                        DSMetricSnapshotTile(item: item, embedded: true)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        if index < items.count - 1 {
                            Rectangle()
                                .fill(AppColors.Stroke.subtle.opacity(0.65))
                                .frame(width: 1, height: AppSpacing.x48 + AppSpacing.x12)
                        }
                    }
                }

                VStack(alignment: .leading, spacing: AppSpacing.x4) {
                    ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                        DSMetricSnapshotTile(item: item, embedded: true)

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
                        DSMetricSnapshotTile(item: item, embedded: false)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    ForEach(items) { item in
                        DSMetricSnapshotTile(item: item, embedded: false)
                    }
                }
            }
        }
    }
}

struct DSExplainabilityCard: View {
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
    private var isIntegrated: Bool {
        cardStyle == .flat
    }

    init(
        eyebrow: String? = nil,
        primaryItems: [Item],
        secondaryItems: [Item] = [],
        footerText: String? = nil,
        style: DSCardStyle = .standard
    ) {
        self.eyebrow = eyebrow
        self.primaryItems = primaryItems
        self.secondaryItems = secondaryItems
        self.footerText = footerText
        self.cardStyle = style
    }

    var body: some View {
        DSCard(style: cardStyle) {
            VStack(alignment: .leading, spacing: AppSpacing.x12) {
                if let eyebrow {
                    Text(eyebrow)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }

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

                if !secondaryItems.isEmpty {
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

                if let footerText {
                    Text(footerText)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }
        }
    }
}

private struct DSMetricSnapshotTile: View {
    let item: DSMetricSnapshotCard.Item
    let embedded: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
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
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(embedded ? AppSpacing.x4 : AppSpacing.x12)
        .frame(minHeight: embedded ? AppSpacing.x40 + AppSpacing.x8 : AppSpacing.x64 + AppSpacing.x12, alignment: .leading)
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
                footerText: "Sleep, HRV, and RHR drive the score. Exertion stays contextual."
            )
        }
        .padding(AppSpacing.x24)
    }
}
