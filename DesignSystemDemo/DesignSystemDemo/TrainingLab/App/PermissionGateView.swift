import SwiftUI

struct PermissionGateView: View {
    enum GateState: Equatable {
        case loading
        case needsPermission
        case ready
        case error(String)
    }

    let environment: AppEnvironment

    @State private var state: GateState = .loading
    var body: some View {
        Group {
            #if os(macOS)
            // macOS enters the real shell directly; HealthKit is a data limitation, not a gate blocker.
            shellView
            #else
            if shouldShowShell {
                shellView
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: AppSpacing.x16) {
                        DSSectionHeader(title: "Phase 3 Permission Gate", actionLabel:  {
                            Text("Online-first")
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                        })

                        content
                    }
                    .padding(AppSpacing.x16)
                }
            }
            #endif
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        #if !os(macOS)
        .task {
            await bootstrap()
        }
        #endif
    }

    private var shouldShowShell: Bool {
        switch state {
        case .ready:
            return true
        case .loading, .needsPermission, .error:
            return false
        }
    }

    @ViewBuilder
    private var shellView: some View {
        TrainingLabShellView(environment: environment)
    }

    @ViewBuilder
    private var content: some View {
        switch state {
        case .loading:
            DSLoadingState()

        case .needsPermission:
            VStack(spacing: AppSpacing.x12) {
                DSEmptyState(
                    iconSystemName: "heart.text.square",
                    title: "Health access required",
                    message: "Allow HealthKit access to continue online-first sync."
                )

                retryCard(label: "Retry")
            }

        case .ready:
            EmptyView()

        case let .error(message):
            VStack(spacing: AppSpacing.x12) {
                DSEmptyState(
                    iconSystemName: "exclamationmark.triangle.fill",
                    title: "Sync failed",
                    message: message
                )

                retryCard(label: "Retry")
            }
        }
    }

    private func retryCard(label: String) -> some View {
        DSCard {
            Button {
                Task {
                    await bootstrap()
                }
            } label: {
                Text(label)
                    .appTextStyle(AppTypography.buttonMedium)
                    .foregroundStyle(AppColors.Accent.orange)
            }
            .buttonStyle(.plain)
        }
    }

    private func bootstrap() async {
        state = .loading
        await environment.ingestionOrchestrator.runInitialSyncIfNeeded()

        do {
            let syncState = try environment.syncStateStore.loadOrCreate()
            let lastError = syncState.lastError?.trimmingCharacters(in: .whitespacesAndNewlines)

            if let lastError, !lastError.isEmpty {
                state = .error(lastError)
                return
            }

            switch syncState.healthAuthStatusRaw {
            case "authorized":
                state = .ready
            case "denied", "notDetermined":
                state = .needsPermission
            case "unsupported":
                state = .error("HealthKit unsupported on this platform")
            default:
                state = .error("Sync state unavailable")
            }
        } catch {
            state = .error(error.localizedDescription)
        }
    }

}

#Preview {
    PermissionGateView(environment: .stub())
}
