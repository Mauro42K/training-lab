import SwiftUI

struct DSMetricPill: View {
    enum Variant {
        case neutral
        case info
        case success
        case warning
        case danger

        var foregroundColor: Color {
            switch self {
            case .neutral:
                AppColors.Text.primary
            case .info:
                AppColors.Accent.blue
            case .success:
                AppColors.Accent.green
            case .warning:
                AppColors.Accent.orange
            case .danger:
                AppColors.Accent.red
            }
        }
    }

    private let title: String
    private let iconSystemName: String?
    private let variant: Variant

    init(_ title: String, iconSystemName: String? = nil, variant: Variant = .neutral) {
        self.title = title
        self.iconSystemName = iconSystemName
        self.variant = variant
    }

    var body: some View {
        HStack(spacing: AppSpacing.x8) {
            if let iconSystemName {
                Image(systemName: iconSystemName)
                    .appTextStyle(AppTypography.labelSmall)
            }

            Text(title)
                .appTextStyle(AppTypography.labelSmall)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .foregroundStyle(variant.foregroundColor)
        .padding(.horizontal, AppSpacing.x12)
        .padding(.vertical, AppSpacing.x8)
        .background(AppColors.Surface.cardMuted)
        .clipShape(Capsule(style: .continuous))
        .overlay(Capsule(style: .continuous).stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline))
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        HStack(spacing: AppSpacing.x12) {
            DSMetricPill("Neutral")
            DSMetricPill("Up", iconSystemName: "arrow.up", variant: .success)
            DSMetricPill("Alert", iconSystemName: "exclamationmark.triangle.fill", variant: .warning)
        }
        .padding()
    }
}
