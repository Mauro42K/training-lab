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
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") {
                                showGallery = false
                            }
                        }
                    }
            }
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
