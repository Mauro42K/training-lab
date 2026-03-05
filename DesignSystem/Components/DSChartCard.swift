import SwiftUI

struct DSChartCard<ChartContent: View>: View {
    struct LegendItem: Identifiable {
        let id = UUID()
        let title: String
        let color: Color
    }

    enum Style {
        case standard
        case emphasized

        var cardStyle: DSCardStyle {
            switch self {
            case .standard:
                .standard
            case .emphasized:
                .floating
            }
        }
    }

    private let title: String
    private let subtitle: String?
    private let legendItems: [LegendItem]
    private let style: Style
    private let chartContent: ChartContent

    init(
        title: String,
        subtitle: String? = nil,
        style: Style = .standard,
        legendItems: [LegendItem] = [],
        @ViewBuilder chartContent: () -> ChartContent
    ) {
        self.title = title
        self.subtitle = subtitle
        self.legendItems = legendItems
        self.style = style
        self.chartContent = chartContent()
    }

    var body: some View {
        DSCard(style: style.cardStyle, minHeight: AppChartStyle.Layout.cardMinHeight) {
            VStack(alignment: .leading, spacing: AppChartStyle.Layout.contentSpacing) {
                VStack(alignment: .leading, spacing: AppSpacing.x4) {
                    Text(title)
                        .appTextStyle(AppTypography.headingH3)
                        .foregroundStyle(AppColors.Text.primary)

                    if let subtitle {
                        Text(subtitle)
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    }
                }

                if !legendItems.isEmpty {
                    HStack(spacing: AppSpacing.x12) {
                        ForEach(legendItems) { item in
                            HStack(spacing: AppSpacing.x8) {
                                Circle()
                                    .fill(item.color)
                                    .frame(width: AppSpacing.x8, height: AppSpacing.x8)

                                Text(item.title)
                                    .appTextStyle(AppChartStyle.Axis.labelStyle)
                                    .foregroundStyle(AppChartStyle.Axis.labelColor)
                            }
                        }
                    }
                }

                chartContent
                    .frame(maxWidth: .infinity, minHeight: AppChartStyle.Layout.plotMinHeight, alignment: .bottomLeading)
                    .padding(.top, AppChartStyle.Layout.plotTopPadding)
                    .padding(.bottom, AppChartStyle.Layout.plotBottomPadding)
            }
        }
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        DSChartCard(
            title: "Training Load",
            subtitle: "Last 7 days",
            legendItems: [
                .init(title: "TRIMP", color: AppChartStyle.Series.primary),
                .init(title: "Recovery", color: AppChartStyle.Series.secondary)
            ]
        ) {
            RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                .fill(AppChartStyle.Series.primary.opacity(AppChartStyle.Series.fillOpacity))
                .overlay(
                    RoundedRectangle(cornerRadius: AppRadius.medium, style: .continuous)
                        .stroke(AppChartStyle.Grid.lineColor, lineWidth: AppChartStyle.Grid.lineWidth)
                )
        }
        .padding()
    }
}
