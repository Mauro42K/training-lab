import SwiftUI

struct PermissionGateView: View {
    enum GateState: Equatable {
        case loading
        case needsPermission
        case ready
        case error(String)
    }

    let environment: AppEnvironment
    let openGallery: () -> Void

    @State private var state: GateState = .loading

    var body: some View {
        Group {
            if shouldShowTrainingLoad {
                TrainingLoadScreen(environment: environment)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: AppSpacing.x16) {
                        DSSectionHeader(title: "Phase 3 Permission Gate", actionLabel:  {
                            Text("Online-first")
                                .appTextStyle(AppTypography.labelSmall)
                                .foregroundStyle(AppColors.Text.secondary)
                        })

                        content

                        DSCard(style: .muted) {
                            VStack(alignment: .leading, spacing: AppSpacing.x12) {
                                Text("Demo access")
                                    .appTextStyle(AppTypography.headingH3)
                                    .foregroundStyle(AppColors.Text.primary)

                                Text("Open Design System Gallery while sync pipelines are bootstrapping.")
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
            }
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .task {
            await bootstrap()
        }
    }

    private var shouldShowTrainingLoad: Bool {
        switch state {
        case .ready, .error:
            return true
        case .loading, .needsPermission:
            return false
        }
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
    PermissionGateView(environment: .stub(), openGallery: {})
}
