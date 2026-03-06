import SwiftUI

struct TrainingLoadSummaryRow: View {
    let today: Double
    let sevenDays: Double
    let twentyEightDays: Double

    var body: some View {
        DSCard(style: .floating) {
            HStack(spacing: AppSpacing.x12) {
                TrainingLoadSummaryMetric(title: "Today", value: today, isPrimary: true)
                divider
                TrainingLoadSummaryMetric(title: "7d", value: sevenDays, isPrimary: false)
                divider
                TrainingLoadSummaryMetric(title: "28d", value: twentyEightDays, isPrimary: false)
            }
        }
    }

    private var divider: some View {
        Rectangle()
            .fill(AppColors.Stroke.subtle)
            .frame(width: 1, height: AppSpacing.x24)
    }
}

private struct TrainingLoadSummaryMetric: View {
    let title: String
    let value: Double
    let isPrimary: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x4) {
            Text(title)
                .appTextStyle(isPrimary ? AppTypography.buttonMedium : AppTypography.labelSmall)
                .foregroundStyle(isPrimary ? AppColors.Text.primary : AppColors.Text.secondary)
            Text(String(Int(value.rounded())))
                .appTextStyle(isPrimary ? AppTypography.headingH2 : AppTypography.headingH3)
                .foregroundStyle(isPrimary ? AppColors.Accent.blue : AppColors.Text.primary)
                .monospacedDigit()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
