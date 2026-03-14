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
        }
        .padding(AppSpacing.x24)
    }
}
