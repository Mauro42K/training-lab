import SwiftUI

struct SectionPlaceholderView: View {
    let section: TrainingLabSection

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                DSSectionHeader(title: section.title, actionLabel: {
                    DSMetricPill(section.sectionStateTitle, variant: section.sectionStateVariant)
                })

                DSCard(style: .flat, minHeight: 240) {
                    VStack(alignment: .leading, spacing: AppSpacing.x16) {
                        HStack(alignment: .center, spacing: AppSpacing.x12) {
                            ZStack {
                                Circle()
                                    .fill(section.sectionStateVariant.foregroundColor.opacity(0.14))
                                    .frame(width: 44, height: 44)

                                Image(systemName: section.symbolName)
                                    .font(.system(size: 18, weight: .semibold))
                                    .foregroundStyle(section.sectionStateVariant.foregroundColor)
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text(section.placeholderHeadline)
                                    .appTextStyle(AppTypography.headingH2)
                                    .foregroundStyle(AppColors.Text.primary)

                                Text(section.subtitle)
                                    .appTextStyle(AppTypography.bodySmall)
                                    .foregroundStyle(AppColors.Text.secondary)
                            }
                        }

                        Text(section.placeholderBody)
                            .appTextStyle(AppTypography.bodyRegular)
                            .foregroundStyle(AppColors.Text.secondary)
                            .fixedSize(horizontal: false, vertical: true)

                        VStack(alignment: .leading, spacing: AppSpacing.x8) {
                            ForEach(section.placeholderBullets, id: \.self) { bullet in
                                bulletRow(text: bullet)
                            }
                        }

                        HStack(spacing: AppSpacing.x8) {
                            DSMetricPill("Product foundation", variant: .info)
                            DSMetricPill(section.sectionStateTitle, variant: section.sectionStateVariant)
                        }
                        .accessibilityElement(children: .combine)
                    }
                }
            }
            .padding(AppSpacing.x16)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .navigationTitle(section.title)
    }

    private func bulletRow(text: String) -> some View {
        HStack(alignment: .top, spacing: AppSpacing.x8) {
            Circle()
                .fill(AppColors.Accent.blue)
                .frame(width: 6, height: 6)
                .padding(.top, AppSpacing.x8)

            Text(text)
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 0)
        }
    }
}

#Preview {
    SectionPlaceholderView(section: .workouts)
        .preferredColorScheme(.dark)
}
