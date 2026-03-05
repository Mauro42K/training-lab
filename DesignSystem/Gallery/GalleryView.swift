import SwiftUI

struct GalleryView: View {
    @State private var segmentedSelection = 0

    private let colorItems: [ColorItem] = [
        ColorItem(name: "bgPrimary", color: AppColors.Background.primary),
        ColorItem(name: "bgElevated", color: AppColors.Background.elevated),
        ColorItem(name: "surfaceCard", color: AppColors.Surface.card),
        ColorItem(name: "surfaceCardMuted", color: AppColors.Surface.cardMuted),
        ColorItem(name: "textPrimary", color: AppColors.Text.primary),
        ColorItem(name: "textSecondary", color: AppColors.Text.secondary),
        ColorItem(name: "strokeSubtle", color: AppColors.Stroke.subtle),
        ColorItem(name: "accentBlue", color: AppColors.Accent.blue),
        ColorItem(name: "accentGreen", color: AppColors.Accent.green),
        ColorItem(name: "accentOrange", color: AppColors.Accent.orange),
        ColorItem(name: "accentRed", color: AppColors.Accent.red),
        ColorItem(name: "accentPurple", color: AppColors.Accent.purple)
    ]

    private let spacingItems: [CGFloat] = [
        AppSpacing.x0,
        AppSpacing.x4,
        AppSpacing.x8,
        AppSpacing.x12,
        AppSpacing.x16,
        AppSpacing.x24,
        AppSpacing.x32,
        AppSpacing.x40,
        AppSpacing.x48,
        AppSpacing.x64
    ]

    private let radiusItems: [(String, CGFloat)] = [
        ("none", AppRadius.none),
        ("small", AppRadius.small),
        ("medium", AppRadius.medium),
        ("large", AppRadius.large),
        ("xLarge", AppRadius.xLarge),
        ("pill", AppRadius.pill)
    ]

    private let shadowItems: [(String, AppShadow?)] = [
        ("flat", AppElevation.flat.shadow),
        ("card", AppShadows.card),
        ("dropdown", AppShadows.dropdown),
        ("modal", AppShadows.modal)
    ]

    private let typographyItems: [(String, AppTextStyle)] = [
        ("Display / Large", AppTypography.displayLarge),
        ("Display / Medium", AppTypography.displayMedium),
        ("Heading / H1", AppTypography.headingH1),
        ("Heading / H2", AppTypography.headingH2),
        ("Heading / H3", AppTypography.headingH3),
        ("Body / Large", AppTypography.bodyLarge),
        ("Body / Regular", AppTypography.bodyRegular),
        ("Body / Small", AppTypography.bodySmall),
        ("Button / Medium", AppTypography.buttonMedium),
        ("Label / Small", AppTypography.labelSmall)
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x32) {
                DSSectionHeader(title: "Gallery", actionLabel: {
                    Text("Design System")
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                })

                tokenSection
                componentSection
                compositionSection
            }
            .padding(AppSpacing.x16)
            .frame(maxWidth: 960, alignment: .leading)
            .frame(maxWidth: .infinity)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
    }

    private var tokenSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x16) {
            DSSectionHeader(title: "Tokens")

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("Colors")

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 140), spacing: AppSpacing.x12)], spacing: AppSpacing.x12) {
                        ForEach(colorItems) { item in
                            VStack(alignment: .leading, spacing: AppSpacing.x8) {
                                RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                                    .fill(item.color)
                                    .frame(height: AppSpacing.x48)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                                            .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                                    )

                                Text(item.name)
                                    .appTextStyle(AppTypography.labelSmall)
                                    .foregroundStyle(AppColors.Text.secondary)
                            }
                        }
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    tokenSubheader("Typography")

                    ForEach(Array(typographyItems.enumerated()), id: \.offset) { _, item in
                        typographySample(item.0, style: item.1)
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    tokenSubheader("Spacing")

                    ForEach(spacingItems, id: \.self) { value in
                        HStack(spacing: AppSpacing.x12) {
                            Text("\(Int(value))")
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                                .frame(width: AppSpacing.x40, alignment: .leading)

                            RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                                .fill(AppColors.Accent.blue.opacity(AppChartStyle.Series.fillOpacity))
                                .frame(width: max(value * AppSpacing.x4, AppStrokeWidth.hairline), height: AppSpacing.x12)
                        }
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    tokenSubheader("Radius")

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 120), spacing: AppSpacing.x12)], spacing: AppSpacing.x12) {
                        ForEach(radiusItems, id: \.0) { label, value in
                            VStack(alignment: .leading, spacing: AppSpacing.x8) {
                                RoundedRectangle(cornerRadius: value, style: .continuous)
                                    .fill(AppColors.Surface.cardMuted)
                                    .frame(height: AppSpacing.x48 + AppSpacing.x4)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: value, style: .continuous)
                                            .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                                    )

                                Text("\(label) (\(Int(value)))")
                                    .appTextStyle(AppTypography.labelSmall)
                                    .foregroundStyle(AppColors.Text.secondary)
                            }
                        }
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    tokenSubheader("Shadows / Elevation")

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 160), spacing: AppSpacing.x16)], spacing: AppSpacing.x16) {
                        ForEach(shadowItems, id: \.0) { label, shadow in
                            VStack(alignment: .leading, spacing: AppSpacing.x8) {
                                RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                                    .fill(AppColors.Surface.card)
                                    .frame(height: AppSpacing.x64)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                                            .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
                                    )
                                    .appShadow(shadow)

                                Text(label)
                                    .appTextStyle(AppTypography.labelSmall)
                                    .foregroundStyle(AppColors.Text.secondary)
                            }
                        }
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    tokenSubheader("Chart Rules v0.1")

                    VStack(alignment: .leading, spacing: AppSpacing.x8) {
                        Text("Grid")
                            .appTextStyle(AppTypography.buttonMedium)
                            .foregroundStyle(AppColors.Text.primary)
                        Text("Line width \(Int(AppChartStyle.Grid.lineWidth)), \(AppChartStyle.Grid.rowCount) rows, subtle stroke color.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)

                        Text("Axes & Labels")
                            .appTextStyle(AppTypography.buttonMedium)
                            .foregroundStyle(AppColors.Text.primary)
                        Text("Axis labels use Label / Small and secondary text color.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)

                        Text("Interaction")
                            .appTextStyle(AppTypography.buttonMedium)
                            .foregroundStyle(AppColors.Text.primary)
                        Text("Highlight uses accent color and regular stroke width.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    }
                }
            }
        }
    }

    private var componentSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x16) {
            DSSectionHeader(title: "Components")

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("DSCard")
                    DSCard(style: .standard) {
                        Text("Standard Card")
                            .appTextStyle(AppTypography.headingH3)
                            .foregroundStyle(AppColors.Text.primary)
                    }
                    DSCard(style: .floating) {
                        Text("Floating Card")
                            .appTextStyle(AppTypography.bodyRegular)
                            .foregroundStyle(AppColors.Text.secondary)
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("DSMetricPill")
                    HStack(spacing: AppSpacing.x8) {
                        DSMetricPill("Neutral")
                        DSMetricPill("+12%", iconSystemName: "arrow.up", variant: .success)
                        DSMetricPill("High", iconSystemName: "exclamationmark.triangle.fill", variant: .warning)
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("DSSectionHeader")
                    DSSectionHeader(title: "Recent Workouts", action: {}) {
                        Text("See all")
                            .appTextStyle(AppTypography.buttonMedium)
                            .foregroundStyle(AppColors.Accent.blue)
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("DSSegmentedControl")
                    DSSegmentedControl(options: ["Week", "Month", "Year"], selection: $segmentedSelection)
                }
            }

            DSChartCard(
                title: "DSChartCard",
                subtitle: "Tokenized chart container",
                legendItems: [
                    .init(title: "TRIMP", color: AppChartStyle.Series.primary),
                    .init(title: "Recovery", color: AppChartStyle.Series.secondary)
                ]
            ) {
                chartMock
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("DSRing")
                    HStack(spacing: AppSpacing.x16) {
                        DSRing(progress: 0.38, size: .small)
                        DSRing(progress: 0.64, size: .medium, progressColor: AppColors.Accent.green)
                        DSRing(progress: 0.87, size: .large, progressColor: AppColors.Accent.orange)
                    }
                }
            }

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x16) {
                    tokenSubheader("Empty / Loading States")
                    DSEmptyState(
                        iconSystemName: "figure.run",
                        title: "No activity available",
                        message: "When you log your next workout, results will appear here."
                    )
                    DSLoadingState()
                }
            }
        }
    }

    private var compositionSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x16) {
            DSSectionHeader(title: "Compositions (Sandbox)")

            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    Text("Example Metric Card")
                        .appTextStyle(AppTypography.headingH3)
                        .foregroundStyle(AppColors.Text.primary)

                    HStack(spacing: AppSpacing.x8) {
                        DSMetricPill("Load +8%", iconSystemName: "arrow.up", variant: .info)
                        DSMetricPill("Recovered", iconSystemName: "heart.fill", variant: .success)
                    }

                    Text("Weekly training load stays within target range.")
                        .appTextStyle(AppTypography.bodySmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }

            DSChartCard(
                title: "Example Workout Card",
                subtitle: "Chart card composition",
                style: .emphasized,
                legendItems: [
                    .init(title: "Session", color: AppChartStyle.Series.primary)
                ]
            ) {
                chartMock
            }

            DSCard(style: .muted) {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    Text("Example Calendar Card")
                        .appTextStyle(AppTypography.headingH3)
                        .foregroundStyle(AppColors.Text.primary)

                    Text("Calendar shell only. No feature screen behavior in Phase 2.")
                        .appTextStyle(AppTypography.bodySmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }
        }
    }

    private var chartMock: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            ZStack(alignment: .bottomLeading) {
                VStack(spacing: AppSpacing.x12) {
                    ForEach(0..<AppChartStyle.Grid.rowCount, id: \.self) { _ in
                        Rectangle()
                            .fill(AppChartStyle.Grid.lineColor)
                            .frame(height: AppChartStyle.Grid.lineWidth)
                    }
                }

                HStack(alignment: .bottom, spacing: AppSpacing.x8) {
                    ForEach(mockBarHeights.indices, id: \.self) { index in
                        RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
                            .fill(index == mockBarHeights.count - 1 ? AppChartStyle.Series.primary : AppChartStyle.Series.primary.opacity(AppChartStyle.Series.fillOpacity))
                            .frame(width: AppSpacing.x12, height: mockBarHeights[index])
                    }
                }
                .padding(.horizontal, AppSpacing.x8)
                .padding(.bottom, AppSpacing.x4)
            }
            .frame(minHeight: AppChartStyle.Layout.plotMinHeight)

            HStack {
                Text("Mon")
                Spacer()
                Text("Sun")
            }
            .appTextStyle(AppChartStyle.Axis.labelStyle)
            .foregroundStyle(AppChartStyle.Axis.labelColor)
        }
    }

    private var mockBarHeights: [CGFloat] {
        [
            AppSpacing.x24,
            AppSpacing.x32,
            AppSpacing.x16,
            AppSpacing.x40,
            AppSpacing.x48,
            AppSpacing.x24,
            AppSpacing.x64
        ]
    }

    private func tokenSubheader(_ title: String) -> some View {
        Text(title)
            .appTextStyle(AppTypography.headingH3)
            .foregroundStyle(AppColors.Text.primary)
    }

    private func typographySample(_ title: String, style: AppTextStyle) -> some View {
        Text(title)
            .appTextStyle(style)
            .foregroundStyle(AppColors.Text.primary)
            .fixedSize(horizontal: false, vertical: true)
    }
}

private struct ColorItem: Identifiable {
    let id = UUID()
    let name: String
    let color: Color
}

#Preview("iPhone") {
    GalleryView()
}

#Preview("Mac") {
    GalleryView()
        .frame(width: 1000, height: 900)
}
