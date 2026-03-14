import SwiftUI

struct TrainingLoadScreen: View {
    let environment: AppEnvironment

    @State private var selectedFilter: TrainingLoadSportFilter = .all
    @State private var trendSnapshot = TrainingLoadFetchResult.empty(baseURL: URL(string: "https://api.training-lab.mauro42k.com")!)
    @State private var homeSummary: HomeSummaryDTO?
    @State private var selectedDay: SelectedTrainingLoadDay?
    @State private var dayWorkouts: [WorkoutDTO] = []
    @State private var isLoading = false
    @State private var isLoadingDay = false
    @State private var hasLoadedOnce = false
    @State private var errorMessage: String?
    @State private var readinessErrorMessage: String?

    private let calendar = Calendar.current

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                if isLoading && !hasLoadedOnce {
                    DSLoadingState()
                } else {
                    ReadinessHeroSection(
                        date: homeSummary?.date ?? Date(),
                        readiness: homeSummary?.readiness,
                        errorMessage: readinessErrorMessage
                    )

                    CoreMetricsSection(coreMetrics: homeSummary?.coreMetrics)

                    DSSectionHeader(title: "Load Trend", actionLabel: {
                        Text("Last 28 days")
                            .appTextStyle(AppTypography.labelSmall)
                            .foregroundStyle(AppColors.Text.secondary)
                    })

                    TrainingLoadSummaryRow(
                        today: todayTotal,
                        sevenDays: sevenDayTotal,
                        twentyEightDays: twentyEightDayTotal
                    )

                    TrainingLoadFilterControl(selection: $selectedFilter)

                    if let freshnessMessage {
                        TrendFreshnessCard(
                            message: freshnessMessage,
                            source: trendSnapshot.freshness.source
                        )
                    }

                    if shouldShowDiagnostics {
                        TrendDiagnosticsRow(freshness: trendSnapshot.freshness)
                    }

                    TrainingLoadTrendCard(
                        summary: trendSummary,
                        points: chartPoints,
                        onSelectDay: { day in
                            Task { await selectDay(day) }
                        }
                    )
                    .opacity(isLoading ? 0.72 : 1)
                    .animation(.easeInOut(duration: 0.2), value: isLoading)
                }

                if let errorMessage {
                    DSCard(style: .muted) {
                        HStack(spacing: AppSpacing.x8) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(AppColors.Accent.orange)
                            Text(errorMessage)
                                .appTextStyle(AppTypography.bodySmall)
                                .foregroundStyle(AppColors.Text.secondary)
                        }
                    }
                }
            }
            .padding(AppSpacing.x16)
        }
        .background(AppColors.Background.primary.ignoresSafeArea())
        .navigationTitle("Home")
        .task(id: selectedFilter) {
            await loadSeries()
        }
        .sheet(item: $selectedDay, onDismiss: clearSelectedDaySelection) { selection in
            TrainingLoadDayDetailSheet(
                day: selection.date,
                workouts: dayWorkouts,
                isLoading: isLoadingDay
            )
        }
    }

    private var sortedPoints: [TrainingLoadItemDTO] {
        trendSummary.items.sorted { $0.date < $1.date }
    }

    private var chartPoints: [TrainingLoadChartPoint] {
        sortedPoints.map { item in
            TrainingLoadChartPoint(
                id: item.date,
                date: item.date,
                load: item.load,
                capacity: item.capacity,
                isToday: calendar.isDateInToday(item.date),
                isSelected: selectedDay.map { calendar.isDate($0.date, inSameDayAs: item.date) } ?? false
            )
        }
    }

    private var todayTotal: Double {
        trailingCalendarWindowTotal(days: 1)
    }

    private var sevenDayTotal: Double {
        trailingCalendarWindowTotal(days: 7)
    }

    private var twentyEightDayTotal: Double {
        trailingCalendarWindowTotal(days: 28)
    }

    private func loadSeries() async {
        isLoading = true
        defer { isLoading = false }

        async let trendResult = Self.capture {
            try await environment.trainingLoadRepository.getTrainingLoad(
                days: 28,
                sport: selectedFilter
            )
        }
        async let homeSummaryResult = Self.capture {
            try await environment.homeSummaryRepository.getHomeSummary(date: Date())
        }

        switch await trendResult {
        case let .success(snapshot):
            trendSnapshot = snapshot
            errorMessage = nil
        case let .failure(error):
            trendSnapshot = .empty(baseURL: environment.apiBaseURL)
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }

        switch await homeSummaryResult {
        case let .success(summary):
            homeSummary = summary
            readinessErrorMessage = nil
        case let .failure(error):
            homeSummary = nil
            readinessErrorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }

        hasLoadedOnce = true
    }

    private func selectDay(_ day: Date) async {
        selectedDay = SelectedTrainingLoadDay(date: day)
        isLoadingDay = true
        defer { isLoadingDay = false }

        do {
            let start = calendar.startOfDay(for: day)
            let end = calendar.date(byAdding: .day, value: 1, to: start)?.addingTimeInterval(-1) ?? start
            let workouts = try await environment.workoutsRepository.getWorkouts(
                from: start,
                to: end,
                sport: selectedFilter.sportType
            )
            if selectedDay.map({ calendar.isDate($0.date, inSameDayAs: day) }) == true {
                dayWorkouts = workouts
            }
        } catch {
            if selectedDay.map({ calendar.isDate($0.date, inSameDayAs: day) }) == true {
                dayWorkouts = []
            }
        }
    }

    private func clearSelectedDaySelection() {
        selectedDay = nil
        dayWorkouts = []
    }

    private var trendSummary: TrainingLoadSummaryDTO {
        trendSnapshot.summary
    }

    private var shouldShowDiagnostics: Bool {
        environment.runtimeEnvironment != .production
    }

    private var freshnessMessage: String? {
        guard let latestPointDate = trendSnapshot.freshness.latestPointDate,
              !calendar.isDateInToday(latestPointDate) else {
            return nil
        }

        let formattedDate = Self.longDateFormatter.string(from: latestPointDate)
        switch trendSnapshot.freshness.source {
        case .remote:
            return "Latest load data is through \(formattedDate)."
        case .cache:
            return "Showing cached load through \(formattedDate) while refresh is unavailable."
        }
    }

    private func trailingCalendarWindowTotal(days: Int) -> Double {
        guard days > 0 else { return 0 }

        let today = calendar.startOfDay(for: Date())
        let windowStart = calendar.date(byAdding: .day, value: -(days - 1), to: today) ?? today

        return sortedPoints.reduce(0) { partial, item in
            let itemDay = calendar.startOfDay(for: item.date)
            guard itemDay >= windowStart && itemDay <= today else {
                return partial
            }
            return partial + item.load
        }
    }

    private static let longDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "MMM d"
        return formatter
    }()

    private static func capture<T>(
        _ operation: @escaping () async throws -> T
    ) async -> Result<T, Error> {
        do {
            return .success(try await operation())
        } catch {
            return .failure(error)
        }
    }
}

private struct SelectedTrainingLoadDay: Identifiable, Equatable {
    let date: Date

    var id: Date { date }
}

private extension TrainingLoadSportFilter {
    var sportType: SportType? {
        switch self {
        case .all:
            return nil
        case .run:
            return .run
        case .bike:
            return .bike
        case .strength:
            return .strength
        case .walk:
            return .walk
        }
    }
}

private struct ReadinessHeroSection: View {
    let date: Date
    let readiness: ReadinessSummaryDTO?
    let errorMessage: String?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x12) {
            Text(Self.dateFormatter.string(from: date))
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)

            Text("Today's Readiness")
                .appTextStyle(AppTypography.headingH2)
                .foregroundStyle(AppColors.Text.primary)

            ReadinessHeroView(
                readiness: readiness,
                errorMessage: errorMessage
            )
        }
    }

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "EEEE, MMM d"
        return formatter
    }()
}

private struct CoreMetricsSection: View {
    let coreMetrics: CoreMetricsSummaryDTO?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x8) {
            Text("Core Metrics")
                .appTextStyle(AppTypography.bodySmall)
                .foregroundStyle(AppColors.Text.secondary)

            CoreMetricsCard(coreMetrics: coreMetrics)
        }
    }
}

private struct CoreMetricsCard: View {
    let coreMetrics: CoreMetricsSummaryDTO?

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .fill(AppColors.Surface.card)

            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [
                            AppColors.Accent.blue.opacity(0.10),
                            AppColors.Accent.blue.opacity(0.02),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            VStack(alignment: .leading, spacing: AppSpacing.x16) {
                HStack(alignment: .top, spacing: AppSpacing.x12) {
                    Text("Current load context")
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)

                    Spacer()

                    if shouldShowStatusPill {
                        statusPill
                    }
                }

                HStack(spacing: AppSpacing.x12) {
                    CoreMetricValueView(
                        title: "7-Day Load",
                        valueText: valueText(for: coreMetrics?.sevenDayLoad),
                        isMuted: shouldDeEmphasizeValues
                    )
                    divider
                    CoreMetricValueView(
                        title: "Fitness",
                        valueText: valueText(for: coreMetrics?.fitness),
                        isMuted: shouldDeEmphasizeValues
                    )
                    divider
                    CoreMetricValueView(
                        title: "Fatigue",
                        valueText: valueText(for: coreMetrics?.fatigue),
                        isMuted: shouldDeEmphasizeValues
                    )
                }

                if let historyCopy {
                    Text(historyCopy)
                        .appTextStyle(AppTypography.labelSmall)
                        .foregroundStyle(AppColors.Text.secondary)
                }
            }
        }
        .padding(AppSpacing.x16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AppColors.Surface.card)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.large, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
        .appShadow(AppShadows.modal)
    }

    private var divider: some View {
        Rectangle()
            .fill(AppColors.Stroke.subtle)
            .frame(width: 1, height: 56)
    }

    private var shouldDeEmphasizeValues: Bool {
        guard let coreMetrics else { return true }
        return coreMetrics.historyStatus == .insufficientHistory || coreMetrics.historyStatus == .missing
    }

    private var historyCopy: String? {
        guard let coreMetrics else {
            return "Load history is unavailable for this block yet."
        }

        switch coreMetrics.historyStatus {
        case .available:
            return nil
        case .partial:
            return "History consolidating."
        case .insufficientHistory:
            return "Limited history so these metrics are still settling."
        case .missing:
            return "Core metrics are waiting for the server snapshot."
        }
    }

    private var shouldShowStatusPill: Bool {
        guard let coreMetrics else { return true }
        return coreMetrics.historyStatus != .available
    }

    @ViewBuilder
    private var statusPill: some View {
        if let coreMetrics {
            switch coreMetrics.historyStatus {
            case .available:
                EmptyView()
            case .partial:
                DSMetricPill("Partial history", iconSystemName: "chart.line.uptrend.xyaxis", variant: .info)
            case .insufficientHistory:
                DSMetricPill("History building", iconSystemName: "clock.arrow.circlepath", variant: .warning)
            case .missing:
                DSMetricPill("Unavailable", iconSystemName: "clock", variant: .warning)
            }
        } else {
            DSMetricPill("Unavailable", iconSystemName: "clock", variant: .warning)
        }
    }

    private func valueText(for value: Double?) -> String {
        guard let value, coreMetrics?.historyStatus != .missing else {
            return "--"
        }
        return String(Int(value.rounded()))
    }
}

private struct CoreMetricValueView: View {
    let title: String
    let valueText: String
    let isMuted: Bool

    var body: some View {
        VStack(alignment: .center, spacing: AppSpacing.x4) {
            Text(title)
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(AppColors.Text.secondary)

            Text(valueText)
                .appTextStyle(AppTypography.headingH1)
                .foregroundStyle(AppColors.Text.primary.opacity(isMuted ? 0.72 : 1))
                .monospacedDigit()
        }
        .frame(maxWidth: .infinity, alignment: .center)
    }
}

private struct ReadinessHeroView: View {
    let readiness: ReadinessSummaryDTO?
    let errorMessage: String?

    private static let heroSurface = Color(
        .sRGB,
        red: 22.0 / 255.0,
        green: 22.0 / 255.0,
        blue: 24.0 / 255.0,
        opacity: 1
    )
    private static let heroPrimaryText = Color.white
    private static let heroSecondaryText = Color.white.opacity(0.64)
    private static let heroTertiaryText = Color.white.opacity(0.5)

    private var theme: ReadinessHeroTheme {
        ReadinessHeroTheme(label: readiness?.label)
    }

    var body: some View {
        ZStack(alignment: .bottom) {
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Self.heroSurface)

            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [theme.wash.opacity(0.24), theme.wash.opacity(0.04)],
                        startPoint: .bottom,
                        endPoint: .top
                    )
                )

            Circle()
                .fill(theme.glow.opacity(0.36))
                .frame(width: 240, height: 240)
                .blur(radius: 72)
                .offset(y: 84)

            WaveBandShape()
                .fill(
                    LinearGradient(
                        colors: [theme.wave.opacity(0.28), theme.wave.opacity(0.08)],
                        startPoint: .bottom,
                        endPoint: .top
                    )
                )
                .frame(height: 118)
                .overlay(alignment: .top) {
                    WaveStrokeShape()
                        .stroke(theme.wave.opacity(0.42), lineWidth: 1)
                        .frame(height: 40)
                        .offset(y: 1)
                }
                .opacity(0.92)

            content
                .padding(.horizontal, AppSpacing.x24)
                .padding(.top, 36)
                .padding(.bottom, 30)
        }
        .frame(maxWidth: .infinity, minHeight: 280, alignment: .top)
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(AppColors.Stroke.subtle, lineWidth: AppStrokeWidth.hairline)
        )
        .appShadow(AppShadows.modal)
    }

    @ViewBuilder
    private var content: some View {
        if let readiness, readiness.completenessStatus != .missing {
            if readiness.completenessStatus == .insufficient {
                insufficientContent(readiness)
            } else {
                standardContent(readiness)
            }
        } else {
            missingContent
        }
    }

    private func standardContent(_ readiness: ReadinessSummaryDTO) -> some View {
        VStack(spacing: AppSpacing.x8) {
            Spacer(minLength: 0)

            HStack(spacing: 0) {
                Text(scoreText(for: readiness.score))
                    .font(.system(size: 82, weight: .bold))
                    .monospacedDigit()
                    .foregroundStyle(theme.primary)

                Text("%")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundStyle(theme.primary)
                    .offset(y: -16)
            }

            Text(labelText(for: readiness))
                .appTextStyle(AppTypography.bodyLarge)
                .foregroundStyle(theme.labelAccent)
                .multilineTextAlignment(.center)

            Text(metadataLine(for: readiness))
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(Self.heroTertiaryText)
                .multilineTextAlignment(.center)

            HStack(spacing: AppSpacing.x8) {
                if readiness.completenessStatus == .partial {
                    ReadinessStateBadge(
                        title: "Partial signal",
                        tint: theme.primary
                    )
                }
                if readiness.hasEstimatedContext {
                    ReadinessStateBadge(
                        title: "Estimated context",
                        tint: theme.primary
                    )
                }
            }

            Text(confidenceLine(for: readiness.confidence))
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(Self.heroSecondaryText)

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity)
    }

    private func insufficientContent(_ readiness: ReadinessSummaryDTO) -> some View {
        VStack(spacing: AppSpacing.x8) {
            Spacer(minLength: 0)

            Text(labelText(for: readiness))
                .font(.system(size: 34, weight: .semibold))
                .foregroundStyle(theme.labelAccent)
                .multilineTextAlignment(.center)

            if let score = readiness.score {
                Text("Estimated score \(score)%")
                    .appTextStyle(AppTypography.labelSmall)
                    .foregroundStyle(theme.primary.opacity(0.56))
            }

            Text(metadataLine(for: readiness))
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(Self.heroTertiaryText)
                .multilineTextAlignment(.center)

            HStack(spacing: AppSpacing.x8) {
                ReadinessStateBadge(
                    title: "Limited signal",
                    tint: theme.primary
                )
                if readiness.hasEstimatedContext {
                    ReadinessStateBadge(
                        title: "Estimated context",
                        tint: theme.primary
                    )
                }
            }

            Text(confidenceLine(for: readiness.confidence))
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(Self.heroSecondaryText)

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity)
    }

    private var missingContent: some View {
        VStack(spacing: AppSpacing.x8) {
            Spacer(minLength: 0)

            Text(errorMessage == nil ? "Readiness unavailable" : "Couldn't refresh readiness")
                .font(.system(size: 28, weight: .semibold))
                .foregroundStyle(Self.heroPrimaryText)
                .multilineTextAlignment(.center)

            Text(
                errorMessage
                ?? "Readiness needs Sleep, HRV, and RHR before a score can be shown."
            )
            .appTextStyle(AppTypography.labelSmall)
            .foregroundStyle(Self.heroSecondaryText)
            .multilineTextAlignment(.center)

            Text("No score is shown until today's signal is available.")
                .appTextStyle(AppTypography.labelSmall)
                .foregroundStyle(Self.heroTertiaryText)

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity)
    }

    private func scoreText(for score: Int?) -> String {
        guard let score else { return "--" }
        return String(score)
    }

    private func labelText(for readiness: ReadinessSummaryDTO) -> String {
        switch readiness.label {
        case .ready:
            return "Ready to Train"
        case .moderate:
            return "Moderate Readiness"
        case .recover:
            return "Recover First"
        case .none:
            return "Readiness"
        }
    }

    private func supportingLine(for readiness: ReadinessSummaryDTO) -> String {
        let present = localizedInputs(readiness.inputsPresent)
        let missing = localizedInputs(readiness.inputsMissing)

        switch readiness.completenessStatus {
        case .complete:
            return "Using \(present)."
        case .partial:
            return missing.isEmpty
                ? "Using \(present)."
                : "Using \(present). Missing \(missing)."
        case .insufficient:
            return "Limited signal today. Using \(present)."
        case .missing:
            return "Readiness needs Sleep, HRV, and RHR."
        }
    }

    private func metadataLine(for readiness: ReadinessSummaryDTO) -> String {
        let supporting = supportingLine(for: readiness)
        guard readiness.completenessStatus != .complete else {
            return localizedInputs(readiness.inputsPresent)
        }
        return supporting
    }

    private func confidenceLine(for confidence: Double) -> String {
        "Confidence \(confidenceText(for: confidence))"
    }

    private func localizedInputs(_ inputs: [String]) -> String {
        let labels = inputs.map { input in
            switch input {
            case "sleep":
                return "Sleep"
            case "hrv":
                return "HRV"
            case "rhr":
                return "RHR"
            default:
                return input.capitalized
            }
        }
        switch labels.count {
        case 0:
            return "today's signal"
        case 1:
            return labels[0]
        case 2:
            return "\(labels[0]) and \(labels[1])"
        default:
            let head = labels.dropLast().joined(separator: ", ")
            return "\(head), and \(labels.last ?? "")"
        }
    }

    private func confidenceText(for confidence: Double) -> String {
        "\(Int((confidence * 100).rounded()))%"
    }
}

private struct ReadinessStateBadge: View {
    let title: String
    let tint: Color

    var body: some View {
        Text(title)
            .appTextStyle(AppTypography.labelSmall)
            .foregroundStyle(Color.white)
            .padding(.horizontal, AppSpacing.x8)
            .padding(.vertical, 6)
            .background(tint.opacity(0.18), in: Capsule())
            .overlay(
                Capsule()
                    .stroke(tint.opacity(0.24), lineWidth: AppStrokeWidth.hairline)
            )
    }
}

private struct ReadinessHeroTheme {
    let primary: Color
    let glow: Color
    let wash: Color
    let wave: Color
    let labelAccent: Color

    init(label: ReadinessLabelDTO?) {
        switch label {
        case .moderate:
            primary = AppColors.Accent.amber
            glow = AppColors.Accent.orange
            wash = AppColors.Accent.amber
            wave = AppColors.Accent.orange
            labelAccent = Color.white
        case .recover:
            primary = AppColors.Accent.coral
            glow = AppColors.Accent.red
            wash = AppColors.Accent.coral
            wave = AppColors.Accent.red
            labelAccent = Color.white
        case .ready:
            primary = AppColors.Accent.green
            glow = AppColors.Accent.green
            wash = AppColors.Accent.green
            wave = AppColors.Accent.green
            labelAccent = Color.white
        case .none:
            primary = Color.white.opacity(0.82)
            glow = Color.white.opacity(0.18)
            wash = Color.white.opacity(0.1)
            wave = Color.white.opacity(0.18)
            labelAccent = Color.white
        }
    }
}

private struct WaveBandShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.minX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.height * 0.52))
        path.addCurve(
            to: CGPoint(x: rect.width * 0.4, y: rect.height * 0.72),
            control1: CGPoint(x: rect.width * 0.12, y: rect.height * 0.46),
            control2: CGPoint(x: rect.width * 0.26, y: rect.height * 0.9)
        )
        path.addCurve(
            to: CGPoint(x: rect.width * 0.7, y: rect.height * 0.44),
            control1: CGPoint(x: rect.width * 0.5, y: rect.height * 0.5),
            control2: CGPoint(x: rect.width * 0.58, y: rect.height * 0.2)
        )
        path.addCurve(
            to: CGPoint(x: rect.maxX, y: rect.height * 0.3),
            control1: CGPoint(x: rect.width * 0.84, y: rect.height * 0.72),
            control2: CGPoint(x: rect.width * 0.92, y: rect.height * 0.12)
        )
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        path.closeSubpath()
        return path
    }
}

private struct WaveStrokeShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.minX, y: rect.height * 0.58))
        path.addCurve(
            to: CGPoint(x: rect.width * 0.4, y: rect.height * 0.72),
            control1: CGPoint(x: rect.width * 0.12, y: rect.height * 0.5),
            control2: CGPoint(x: rect.width * 0.28, y: rect.height * 0.88)
        )
        path.addCurve(
            to: CGPoint(x: rect.width * 0.7, y: rect.height * 0.38),
            control1: CGPoint(x: rect.width * 0.52, y: rect.height * 0.52),
            control2: CGPoint(x: rect.width * 0.58, y: rect.height * 0.16)
        )
        path.addCurve(
            to: CGPoint(x: rect.maxX, y: rect.height * 0.18),
            control1: CGPoint(x: rect.width * 0.82, y: rect.height * 0.66),
            control2: CGPoint(x: rect.width * 0.92, y: rect.height * 0.02)
        )
        return path
    }
}

private struct TrendFreshnessCard: View {
    let message: String
    let source: TrainingLoadDataSource

    var body: some View {
        DSCard(style: .muted) {
            HStack(alignment: .top, spacing: AppSpacing.x8) {
                Image(systemName: source == .cache ? "clock.badge.exclamationmark" : "clock.arrow.circlepath")
                    .foregroundStyle(AppColors.Accent.orange)
                Text(message)
                    .appTextStyle(AppTypography.bodySmall)
                    .foregroundStyle(AppColors.Text.secondary)
            }
        }
    }
}

private struct TrendDiagnosticsRow: View {
    let freshness: TrainingLoadFreshness

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.x4) {
            Text(
                "Source \(freshness.source.rawValue.uppercased()) | Base \(freshness.baseURL.absoluteString)"
            )
            Text(
                "Latest point \(Self.debugDateString(freshness.latestPointDate)) | Cache updated \(Self.debugDateString(freshness.cacheUpdatedAt))"
            )
            if let remoteFailureDescription = freshness.remoteFailureDescription {
                Text("Remote refresh failed: \(remoteFailureDescription)")
            } else {
                Text("Remote refresh succeeded")
            }
        }
        .appTextStyle(AppTypography.labelSmall)
        .foregroundStyle(AppColors.Text.secondary)
    }

    private static func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        return formatter.string(from: date)
    }

    private static let formatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter
    }()
}

private extension TrainingLoadFetchResult {
    static func empty(baseURL: URL) -> TrainingLoadFetchResult {
        TrainingLoadFetchResult(
            summary: TrainingLoadSummaryDTO(
                items: [],
                historyStatus: .missing,
                semanticState: nil,
                latestLoad: 0,
                latestCapacity: 0
            ),
            freshness: TrainingLoadFreshness(
                source: .cache,
                baseURL: baseURL,
                remoteAttempted: false,
                remoteFailureDescription: nil,
                fetchedAt: Date(),
                latestPointDate: nil,
                cacheUpdatedAt: nil
            )
        )
    }
}
