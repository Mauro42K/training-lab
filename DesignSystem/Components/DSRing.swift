import SwiftUI

struct DSRing: View {
    enum Size {
        case small
        case medium
        case large

        var value: CGFloat {
            switch self {
            case .small:
                AppSizing.ringSmall
            case .medium:
                AppSizing.ringMedium
            case .large:
                AppSizing.ringLarge
            }
        }
    }

    private let progress: CGFloat
    private let size: Size
    private let lineWidth: CGFloat
    private let trackColor: Color
    private let progressColor: Color
    private let showsLabel: Bool

    init(
        progress: CGFloat,
        size: Size = .medium,
        lineWidth: CGFloat = AppSizing.ringLineWidth,
        trackColor: Color = AppColors.Surface.cardMuted,
        progressColor: Color = AppColors.Accent.blue,
        showsLabel: Bool = true
    ) {
        self.progress = progress
        self.size = size
        self.lineWidth = lineWidth
        self.trackColor = trackColor
        self.progressColor = progressColor
        self.showsLabel = showsLabel
    }

    private var clampedProgress: CGFloat {
        min(max(progress, 0), 1)
    }

    var body: some View {
        VStack(spacing: AppSpacing.x8) {
            ZStack {
                Circle()
                    .stroke(trackColor, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round, lineJoin: .round))

                Circle()
                    .trim(from: 0, to: clampedProgress)
                    .stroke(progressColor, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round, lineJoin: .round))
                    .rotationEffect(.degrees(-90))
            }
            .frame(width: size.value, height: size.value)

            if showsLabel {
                Text("\(Int((clampedProgress * 100).rounded()))%")
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Progress ring")
        .accessibilityValue("\(Int((clampedProgress * 100).rounded())) percent")
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        HStack(spacing: AppSpacing.x16) {
            DSRing(progress: 0.42, size: .small)
            DSRing(progress: 0.68, size: .medium, progressColor: AppColors.Accent.green)
            DSRing(progress: 0.91, size: .large, progressColor: AppColors.Accent.orange)
        }
        .padding()
    }
}
