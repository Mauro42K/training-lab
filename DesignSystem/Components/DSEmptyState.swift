import SwiftUI

struct DSEmptyState: View {
    let iconSystemName: String
    let title: String
    let message: String

    var body: some View {
        VStack(spacing: AppSpacing.x12) {
            Image(systemName: iconSystemName)
                .appTextStyle(AppTypography.headingH1)
                .foregroundStyle(AppColors.Text.secondary)

            Text(title)
                .appTextStyle(AppTypography.headingH3)
                .foregroundStyle(AppColors.Text.primary)
                .multilineTextAlignment(.center)

            Text(message)
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(AppSpacing.x24)
        .background(AppColors.Surface.card)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        DSEmptyState(
            iconSystemName: "moon.zzz",
            title: "No workouts yet",
            message: "Complete your first session to start seeing trends."
        )
        .padding()
    }
}
