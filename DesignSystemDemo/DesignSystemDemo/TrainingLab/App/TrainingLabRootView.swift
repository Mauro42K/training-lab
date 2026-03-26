import SwiftUI

struct TrainingLabRootView: View {
    let environment: AppEnvironment

    var body: some View {
        PermissionGateView(environment: environment)
    }
}

#Preview {
    TrainingLabRootView(environment: .stub())
}
