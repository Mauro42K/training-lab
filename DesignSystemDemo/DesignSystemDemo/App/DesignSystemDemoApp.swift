import SwiftUI

@MainActor
@main
struct DesignSystemDemoApp: App {
    private let environment = AppEnvironment.live()

    var body: some Scene {
        WindowGroup {
            TrainingLabRootView(environment: environment)
        }
    }
}
