import SwiftUI

struct DSSectionHeader<ActionLabel: View>: View {
    private let title: String
    private let action: (() -> Void)?
    private let actionLabel: ActionLabel

    init(
        title: String,
        action: (() -> Void)? = nil,
        @ViewBuilder actionLabel: () -> ActionLabel = { EmptyView() }
    ) {
        self.title = title
        self.action = action
        self.actionLabel = actionLabel()
    }

    var body: some View {
        HStack(spacing: AppSpacing.x12) {
            Text(title)
                .appTextStyle(AppTypography.headingH3)
                .foregroundStyle(AppColors.Text.primary)
                .lineLimit(2)
                .minimumScaleFactor(0.85)

            Spacer(minLength: AppSpacing.x8)

            if let action {
                Button(action: action) {
                    actionLabel
                }
                .buttonStyle(.plain)
            }
        }
    }
}

#Preview {
    ZStack {
        AppColors.Background.primary.ignoresSafeArea()
        DSSectionHeader(title: "Training Overview", action: {}) {
            Text("See all")
                .appTextStyle(AppTypography.buttonMedium)
                .foregroundStyle(AppColors.Accent.blue)
        }
        .padding()
    }
}
