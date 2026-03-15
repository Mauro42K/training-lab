import SwiftUI

enum DSCardStyle {
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
            .overlay(
                RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                    .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
            )
            .appShadow(elevation.shadow)
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

    init(
        eyebrow: String? = nil,
        items: [Item],
        footerText: String? = nil,
        accessory: AnyView? = nil
    ) {
        self.eyebrow = eyebrow
        self.items = items
        self.footerText = footerText
        self.accessory = accessory
    }

    var body: some View {
        DSCard {
            VStack(alignment: .leading, spacing: AppSpacing.x12) {
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

                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .top, spacing: AppSpacing.x12) {
                        ForEach(items) { item in
                            DSMetricSnapshotTile(item: item)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.x12) {
                        ForEach(items) { item in
                            DSMetricSnapshotTile(item: item)
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

    init(
        eyebrow: String? = nil,
        primaryItems: [Item],
        secondaryItems: [Item] = [],
        footerText: String? = nil
    ) {
        self.eyebrow = eyebrow
        self.primaryItems = primaryItems
        self.secondaryItems = secondaryItems
        self.footerText = footerText
    }

    var body: some View {
        DSCard {
            VStack(alignment: .leading, spacing: AppSpacing.x12) {
                if let eyebrow {
                    Text(eyebrow)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }

                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .top, spacing: AppSpacing.x12) {
                        ForEach(primaryItems) { item in
                            DSExplainabilityTile(item: item)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.x12) {
                        ForEach(primaryItems) { item in
                            DSExplainabilityTile(item: item)
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
                                DSExplainabilityTile(item: item)
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
        .padding(AppSpacing.x12)
        .frame(minHeight: AppSpacing.x64 + AppSpacing.x12, alignment: .leading)
        .background(AppColors.Surface.cardMuted)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
    }

    private var detail: String? {
        item.detail
    }
}

private struct DSExplainabilityTile: View {
    let item: DSExplainabilityCard.Item

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
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppSpacing.x12)
        .background(backgroundColor)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
    }

    private var baselineHint: String? {
        guard item.status == .measured else { return nil }
        return item.baselineHint
    }

    private var backgroundColor: Color {
        item.emphasis == .primary ? AppColors.Surface.cardMuted : AppColors.Background.elevated
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
