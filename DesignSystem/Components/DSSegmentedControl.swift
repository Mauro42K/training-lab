import SwiftUI

struct DSSegmentedControl: View {
    let options: [String]
    @Binding var selection: Int

    var body: some View {
        DSCard(style: .muted) {
            Picker("Segmented", selection: $selection) {
                ForEach(Array(options.enumerated()), id: \.offset) { index, option in
                    Text(option)
                        .appTextStyle(AppTypography.buttonMedium)
                        .tag(index)
                }
            }
            .pickerStyle(.segmented)
            .tint(AppColors.Accent.blue)
            .accessibilityLabel("Segmented control")
        }
    }
}

#Preview {
    StatefulPreviewWrapper(0) { selection in
        ZStack {
            AppColors.Background.primary.ignoresSafeArea()
            DSSegmentedControl(options: ["Week", "Month", "Year"], selection: selection)
                .padding()
        }
    }
}

private struct StatefulPreviewWrapper<Value, Content: View>: View {
    @State private var value: Value
    private let content: (Binding<Value>) -> Content

    init(_ value: Value, @ViewBuilder content: @escaping (Binding<Value>) -> Content) {
        _value = State(initialValue: value)
        self.content = content
    }

    var body: some View {
        content($value)
    }
}
