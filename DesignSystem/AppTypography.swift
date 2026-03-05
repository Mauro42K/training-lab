import SwiftUI

struct AppTextStyle: Equatable {
    let size: CGFloat
    let weight: Font.Weight
    let lineHeight: CGFloat
    let textStyle: Font.TextStyle
    let tracking: CGFloat

    var font: Font {
        Font.system(size: size, weight: weight)
    }

    var lineSpacing: CGFloat {
        max(0, lineHeight - size)
    }
}

enum AppTypography {
    static let displayLarge = AppTextStyle(size: 40, weight: .semibold, lineHeight: 48, textStyle: .largeTitle, tracking: 0)
    static let displayMedium = AppTextStyle(size: 34, weight: .semibold, lineHeight: 41, textStyle: .title, tracking: 0)

    static let headingH1 = AppTextStyle(size: 32, weight: .semibold, lineHeight: 40, textStyle: .title, tracking: 0)
    static let headingH2 = AppTextStyle(size: 28, weight: .semibold, lineHeight: 34, textStyle: .title2, tracking: 0)
    static let headingH3 = AppTextStyle(size: 20, weight: .semibold, lineHeight: 28, textStyle: .title3, tracking: 0)

    static let bodyLarge = AppTextStyle(size: 18, weight: .regular, lineHeight: 26, textStyle: .body, tracking: 0)
    static let bodyRegular = AppTextStyle(size: 16, weight: .regular, lineHeight: 24, textStyle: .body, tracking: 0)
    static let bodySmall = AppTextStyle(size: 14, weight: .regular, lineHeight: 20, textStyle: .subheadline, tracking: 0)

    static let buttonMedium = AppTextStyle(size: 15, weight: .semibold, lineHeight: 20, textStyle: .callout, tracking: 0)
    static let labelSmall = AppTextStyle(size: 12, weight: .medium, lineHeight: 16, textStyle: .caption, tracking: 0)

    // Backward-compatible aliases for current component usage.
    static let heading1 = headingH1
    static let heading2 = headingH2
    static let heading3 = headingH3
    static let heading4 = bodyLarge
    static let body = bodyRegular
    static let button = buttonMedium
    static let label = labelSmall
}

struct AppTextStyleModifier: ViewModifier {
    let style: AppTextStyle

    func body(content: Content) -> some View {
        content
            .font(style.font)
            .lineSpacing(style.lineSpacing)
            .tracking(style.tracking)
    }
}

extension View {
    func appTextStyle(_ style: AppTextStyle) -> some View {
        modifier(AppTextStyleModifier(style: style))
    }
}
