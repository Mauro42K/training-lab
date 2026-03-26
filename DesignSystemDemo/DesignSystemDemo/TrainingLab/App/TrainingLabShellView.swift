import SwiftUI

struct TrainingLabShellView: View {
    let environment: AppEnvironment

    @State private var selectedSection: TrainingLabSection = .home

    var body: some View {
        Group {
            #if os(macOS)
            macShell
            #else
            iphoneShell
            #endif
        }
        .preferredColorScheme(.dark)
    }
}

private extension TrainingLabShellView {
    #if os(macOS)
    var macShell: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            detailView(for: selectedSection)
        }
        .navigationSplitViewStyle(.balanced)
    }
    #endif

    #if !os(macOS)
    var iphoneShell: some View {
        NavigationStack {
            TabView(selection: $selectedSection) {
                ForEach(TrainingLabSection.allCases) { section in
                    sectionView(for: section)
                        .tabItem {
                            Label(section.title, systemImage: section.symbolName)
                        }
                        .tag(section)
                }
            }
        }
    }
    #endif

    #if os(macOS)
    var sidebar: some View {
        List(TrainingLabSection.allCases, selection: $selectedSection) { section in
            SidebarSectionRow(section: section)
                .tag(section)
        }
        .listStyle(.sidebar)
        .navigationTitle("Training Lab")
    }
    #endif

    @ViewBuilder
    func detailView(for section: TrainingLabSection) -> some View {
        sectionView(for: section)
    }

    @ViewBuilder
    func sectionView(for section: TrainingLabSection) -> some View {
        switch section {
        case .home:
            TrainingLoadScreen(environment: environment)

        case .trends:
            TrendsHostView()

        case .workouts, .calendar, .body, .more:
            SectionPlaceholderView(section: section)
        }
    }
}

private struct SidebarSectionRow: View {
    let section: TrainingLabSection

    var body: some View {
        HStack(alignment: .center, spacing: AppSpacing.x12) {
            Image(systemName: section.symbolName)
                .frame(width: AppSpacing.x16)
                .foregroundStyle(section.sectionStateVariant.foregroundColor)

            VStack(alignment: .leading, spacing: 2) {
                Text(section.title)
                    .appTextStyle(AppTypography.bodyRegular)
                    .foregroundStyle(AppColors.Text.primary)

                Text(section.subtitle)
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(AppColors.Text.secondary)
            }

            Spacer(minLength: AppSpacing.x8)

            DSMetricPill(section.sectionStateTitle, variant: section.sectionStateVariant)
        }
        .padding(.vertical, AppSpacing.x4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(section.accessibilityLabel)
    }
}

#Preview("Shell") {
    TrainingLabShellView(environment: .stub())
}
