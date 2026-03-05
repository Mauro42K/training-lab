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
        }
        .padding(AppSpacing.x24)
    }
}
