import SwiftUI

struct TrainingLabRootView: View {
    let environment: AppEnvironment

    @State private var showGallery = false

    var body: some View {
        NavigationStack {
            PermissionGateView(environment: environment) {
                showGallery = true
            }
            .navigationTitle("Training Lab")
            .toolbar {
                #if DEBUG
                ToolbarItem(placement: environmentBadgePlacement) {
                    Text(environment.runtimeEnvironment.badgeLabel)
                        .font(.caption2.weight(.semibold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(.thinMaterial, in: Capsule())
                        .foregroundStyle(environmentBadgeColor)
                        .accessibilityIdentifier("runtime-environment-badge")
                }
                #endif
                ToolbarItem(placement: .primaryAction) {
                    Button("Gallery") {
                        showGallery = true
                    }
                    .appTextStyle(AppTypography.buttonMedium)
                }
            }
        }
        .sheet(isPresented: $showGallery) {
            NavigationStack {
                DesignSystemGalleryView()
                    .toolbar {
                        ToolbarItem(placement: .primaryAction) {
                            Button("Done") {
                                showGallery = false
                            }
                        }
                    }
            }
        }
    }
}

private extension TrainingLabRootView {
    var environmentBadgePlacement: ToolbarItemPlacement {
        #if os(macOS)
        return .navigation
        #else
        return .topBarLeading
        #endif
    }

    var environmentBadgeColor: Color {
        switch environment.runtimeEnvironment {
        case .production:
            return .green
        case .staging:
            return .orange
        case .local:
            return .blue
        }
    }
}

struct DesignSystemGalleryView: View {
    var body: some View {
        GalleryView()
    }
}

#Preview {
    TrainingLabRootView(environment: .stub())
}
