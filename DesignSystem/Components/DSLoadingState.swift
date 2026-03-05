import SwiftUI

struct DSLoadingState: View {
    @State private var shimmerOffset: CGFloat = -1

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x12) {
            SkeletonBlock(width: AppSizing.skeletonTitleWidth, height: AppSizing.skeletonTitleHeight, shimmerOffset: shimmerOffset)
            SkeletonBlock(width: AppSizing.skeletonPrimaryLineWidth, height: AppSizing.skeletonLineHeight, shimmerOffset: shimmerOffset)
            SkeletonBlock(width: AppSizing.skeletonSecondaryLineWidth, height: AppSizing.skeletonLineHeight, shimmerOffset: shimmerOffset)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppSpacing.x16)
        .background(AppColors.Surface.card)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
        .onAppear {
            withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: false)) {
                shimmerOffset = 2
            }
        }
    }
}

private struct SkeletonBlock: View {
    let width: CGFloat
    let height: CGFloat
    let shimmerOffset: CGFloat

    var body: some View {
        RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous)
            .fill(AppColors.Surface.cardMuted)
            .frame(width: width, height: height)
            .overlay {
                GeometryReader { geometry in
                    let gradientWidth = max(
                        geometry.size.width * AppSizing.skeletonShimmerFraction,
                        AppSizing.skeletonShimmerMinWidth
                    )

                    LinearGradient(
                        colors: [
                            Color.clear,
                            AppColors.Stroke.strong.opacity(0.8),
                            Color.clear
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                    .frame(width: gradientWidth)
                    .offset(x: shimmerOffset * geometry.size.width)
                }
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.small, style: .continuous))
            }
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        DSLoadingState()
            .padding()
    }
}
