import SwiftUI

struct TrendsHostView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                DSSectionHeader(title: TrainingLabSection.trends.title, actionLabel: {
                    DSMetricPill("Phase 6.0 scaffold", variant: .info)
                })

                heroCard

                DSCard(style: .muted) {
                    VStack(alignment: .leading, spacing: AppSpacing.x12) {
                        Text("Surface slots reserved")
                            .appTextStyle(AppTypography.headingH3)
                            .foregroundStyle(AppColors.Text.primary)

                        VStack(alignment: .leading, spacing: AppSpacing.x8) {
                            placeholderRow(title: "Trends hero", detail: "Dominant analytical surface for how training evolves.")
                            placeholderRow(title: "Fitness progress", detail: "Long-range progression view.")
                            placeholderRow(title: "Load trend", detail: "Capacity-aware trajectory surface.")
                            placeholderRow(title: "Intensity distribution", detail: "Derived from approved load metrics only.")
                        }
                    }
                }
            }
            .padding(AppSpacing.x16)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .navigationTitle(TrainingLabSection.trends.title)
    }

    private var heroCard: some View {
        DSCard(style: .flat, minHeight: 220) {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                HStack(alignment: .center, spacing: AppSpacing.x12) {
                    ZStack {
                        Circle()
                            .fill(AppColors.Accent.blue.opacity(0.16))
                            .frame(width: 44, height: 44)
                        Image(systemName: TrainingLabSection.trends.symbolName)
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(AppColors.Accent.blue)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Training evolution")
                            .appTextStyle(AppTypography.headingH2)
                            .foregroundStyle(AppColors.Text.primary)

                        Text("The future hero chart will live here.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    }
                }

                Text("Phase 6.0 only establishes the landing surface. The charting stack begins in Phase 6.1, after the shell is stable.")
                    .appTextStyle(AppTypography.bodyRegular)
                    .foregroundStyle(AppColors.Text.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack(spacing: AppSpacing.x8) {
                    DSMetricPill("Load domain", variant: .info)
                    DSMetricPill("Hero chart next", variant: .neutral)
                    DSMetricPill("No charts yet", variant: .warning)
                }
                .accessibilityElement(children: .combine)
            }
        }
    }

    private func placeholderRow(title: String, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .appTextStyle(AppTypography.bodyRegular)
                .foregroundStyle(AppColors.Text.primary)

            Text(detail)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)
        }
    }
}

#Preview {
    TrendsHostView()
        .preferredColorScheme(.dark)
}
