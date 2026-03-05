import CoreGraphics
import SwiftUI

enum AppChartStyle {
    enum Layout {
        static let cardMinHeight: CGFloat = AppSizing.chartMinHeight
        static let plotMinHeight: CGFloat = AppSizing.chartMinHeight
        static let contentSpacing: CGFloat = AppSpacing.x12
        static let plotTopPadding: CGFloat = AppSpacing.x8
        static let plotBottomPadding: CGFloat = AppSpacing.x4
    }

    enum Grid {
        static let lineColor = AppColors.Stroke.subtle
        static let lineWidth: CGFloat = AppStrokeWidth.hairline
        static let rowCount: Int = 4
    }

    enum Axis {
        static let labelStyle = AppTypography.labelSmall
        static let labelColor = AppColors.Text.secondary
    }

    enum Label {
        static let valueStyle = AppTypography.bodySmall
        static let valueColor = AppColors.Text.primary
    }

    enum Series {
        static let primary = AppColors.Accent.blue
        static let secondary = AppColors.Accent.green
        static let tertiary = AppColors.Accent.orange
        static let fillOpacity: Double = 0.22
    }

    enum Interaction {
        static let highlightColor = AppColors.Accent.blue
        static let highlightLineWidth: CGFloat = AppStrokeWidth.regular
        static let markerRadius: CGFloat = AppRadius.small
    }
}
