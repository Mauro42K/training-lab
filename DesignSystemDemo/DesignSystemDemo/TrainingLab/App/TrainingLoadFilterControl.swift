import SwiftUI

struct TrainingLoadFilterControl: View {
    @Binding var selection: TrainingLoadSportFilter

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            DSSegmentedControl(
                options: TrainingLoadSportFilter.allCases.map(\.rawValue),
                selection: Binding(
                    get: {
                        TrainingLoadSportFilter.allCases.firstIndex(of: selection) ?? 0
                    },
                    set: { index in
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selection = TrainingLoadSportFilter.allCases[index]
                        }
                    }
                )
            )

            Text("Filter: \(selection.rawValue.capitalized)")
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentTransition(.opacity)
                .animation(.easeInOut(duration: 0.2), value: selection)
        }
    }
}
