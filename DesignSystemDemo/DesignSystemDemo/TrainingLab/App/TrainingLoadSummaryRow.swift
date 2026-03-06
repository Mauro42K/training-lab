import SwiftUI

struct TrainingLoadSummaryRow: View {
    let today: Double
    let sevenDays: Double
    let twentyEightDays: Double

    var body: some View {
        DSCard(style: .floating) {
            HStack(spacing: AppSpacing.x12) {
                TrainingLoadSummaryMetric(title: "Today", value: today)
                TrainingLoadSummaryMetric(title: "7d", value: sevenDays)
                TrainingLoadSummaryMetric(title: "28d", value: twentyEightDays)
            }
        }
    }
}

private struct TrainingLoadSummaryMetric: View {
    let title: String
    let value: Double

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x4) {
            Text(title)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)
            Text(String(Int(value.rounded())))
                .appTextStyle(AppTypography.headingH2)
                .foregroundStyle(AppColors.Text.primary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
