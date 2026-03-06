import SwiftUI

struct TrainingLoadFilterControl: View {
    @Binding var selection: TrainingLoadSportFilter

    var body: some View {
        DSSegmentedControl(
            options: TrainingLoadSportFilter.allCases.map(\.rawValue),
            selection: Binding(
                get: {
                    TrainingLoadSportFilter.allCases.firstIndex(of: selection) ?? 0
                },
                set: { index in
                    selection = TrainingLoadSportFilter.allCases[index]
                }
            )
        )
    }
}
