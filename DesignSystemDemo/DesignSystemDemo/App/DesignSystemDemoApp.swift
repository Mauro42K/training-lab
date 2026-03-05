import SwiftUI

@main
struct DesignSystemDemoApp: App {
    private let environment = AppEnvironment.stub()

    var body: some Scene {
        WindowGroup {
            TrainingLabRootView(environment: environment)
        }
    }
}

struct TrainingLabRootView: View {
    let environment: AppEnvironment

    @State private var isShowingGallery = false

    var body: some View {
        NavigationStack {
            PermissionGateView(environment: environment) {
                isShowingGallery = true
            }
            .navigationTitle("Training Lab")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Gallery") {
                        isShowingGallery = true
                    }
                    .appTextStyle(AppTypography.buttonMedium)
                }
            }
        }
        .sheet(isPresented: $isShowingGallery) {
            GalleryRootView()
        }
    }
}

struct PermissionGateView: View {
    enum GateState: Equatable {
        case loading
        case needsPermission
        case ready
        case error
    }

    let environment: AppEnvironment
    let openGallery: () -> Void

    @State private var gateState: GateState = .loading
    @State private var syncStateLabel = "Sync: pending"

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                DSSectionHeader(title: "Phase 3 Permission Gate") {
                    Text("Online-first")
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }

                gateBody

                DSCard(style: .muted) {
                    VStack(alignment: .leading, spacing: AppSpacing.x12) {
                        Text("Demo access")
                            .appTextStyle(AppTypography.headingH3)
                            .foregroundStyle(AppColors.Text.primary)

                        Text("Mantiene acceso al Design System demo mientras construimos Training Lab.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)

                        Button(action: openGallery) {
                            Text("Open Design System Gallery")
                                .appTextStyle(AppTypography.buttonMedium)
                                .foregroundStyle(AppColors.Accent.blue)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(AppSpacing.x16)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .task {
            await loadInitialState()
        }
    }

    @ViewBuilder
    private var gateBody: some View {
        switch gateState {
        case .loading:
            DSLoadingState()

        case .needsPermission:
            VStack(spacing: AppSpacing.x12) {
                DSEmptyState(
                    iconSystemName: "heart.text.square",
                    title: "Health access required",
                    message: "Training Lab needs HealthKit permission to ingest workouts."
                )

                DSCard {
                    VStack(alignment: .leading, spacing: AppSpacing.x12) {
                        Text("Grant access to continue")
                            .appTextStyle(AppTypography.headingH3)
                            .foregroundStyle(AppColors.Text.primary)

                        Text("This action will transition to online-first sync setup.")
                            .appTextStyle(AppTypography.bodySmall)
                            .foregroundStyle(AppColors.Text.secondary)

                        Button {
                            Task {
                                await requestPermission()
                            }
                        } label: {
                            Text("Grant Health Permission")
                                .appTextStyle(AppTypography.buttonMedium)
                                .foregroundStyle(AppColors.Accent.green)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

        case .ready:
            DSCard {
                VStack(alignment: .leading, spacing: AppSpacing.x12) {
                    Text("Permissions ready")
                        .appTextStyle(AppTypography.headingH3)
                        .foregroundStyle(AppColors.Text.primary)

                    HStack(spacing: AppSpacing.x8) {
                        DSMetricPill("HealthKit: authorized", iconSystemName: "checkmark.circle.fill", variant: .success)
                        DSMetricPill(syncStateLabel, iconSystemName: "arrow.triangle.2.circlepath", variant: .info)
                    }

                    Text("Phase 3 shell is ready for SyncClient wiring in next blocks.")
                        .appTextStyle(AppTypography.bodySmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }

        case .error:
            VStack(spacing: AppSpacing.x12) {
                DSEmptyState(
                    iconSystemName: "exclamationmark.triangle.fill",
                    title: "Permission check failed",
                    message: "Retry the permission bootstrap flow."
                )

                DSCard {
                    Button {
                        Task {
                            await loadInitialState()
                        }
                    } label: {
                        Text("Retry")
                            .appTextStyle(AppTypography.buttonMedium)
                            .foregroundStyle(AppColors.Accent.orange)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func loadInitialState() async {
        gateState = .loading

        do {
            let status = try await environment.healthPermissionClient.currentStatus()
            syncStateLabel = environment.syncState.currentLabel

            switch status {
            case .authorized:
                gateState = .ready
            case .denied, .notDetermined:
                gateState = .needsPermission
            }
        } catch {
            gateState = .error
        }
    }

    private func requestPermission() async {
        do {
            let status = try await environment.healthPermissionClient.requestAuthorization()
            syncStateLabel = environment.syncState.currentLabel

            switch status {
            case .authorized:
                gateState = .ready
            case .denied, .notDetermined:
                gateState = .needsPermission
            }
        } catch {
            gateState = .error
        }
    }
}

struct AppEnvironment {
    let healthPermissionClient: HealthPermissionClient
    let syncState: SyncState

    static func stub() -> AppEnvironment {
        AppEnvironment(
            healthPermissionClient: StubHealthPermissionClient(),
            syncState: SyncState(currentLabel: "Sync: idle")
        )
    }
}

struct SyncState {
    let currentLabel: String
}

enum HealthPermissionStatus {
    case notDetermined
    case authorized
    case denied
}

protocol HealthPermissionClient {
    func currentStatus() async throws -> HealthPermissionStatus
    func requestAuthorization() async throws -> HealthPermissionStatus
}

struct StubHealthPermissionClient: HealthPermissionClient {
    func currentStatus() async throws -> HealthPermissionStatus {
        try await Task.sleep(nanoseconds: 200_000_000)
        return .notDetermined
    }

    func requestAuthorization() async throws -> HealthPermissionStatus {
        try await Task.sleep(nanoseconds: 200_000_000)
        return .authorized
    }
}

#Preview {
    TrainingLabRootView(environment: .stub())
}
