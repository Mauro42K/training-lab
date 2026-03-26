import SwiftUI

enum TrainingLabSection: String, CaseIterable, Identifiable, Hashable, Sendable {
    case home
    case trends
    case workouts
    case calendar
    case body
    case more

    var id: String { rawValue }

    var title: String {
        switch self {
        case .home:
            return "Home"
        case .trends:
            return "Trends"
        case .workouts:
            return "Workouts"
        case .calendar:
            return "Calendar"
        case .body:
            return "Body"
        case .more:
            return "More"
        }
    }

    var symbolName: String {
        switch self {
        case .home:
            return "house.fill"
        case .trends:
            return "chart.line.uptrend.xyaxis"
        case .workouts:
            return "figure.run"
        case .calendar:
            return "calendar"
        case .body:
            return "figure.strengthtraining.traditional"
        case .more:
            return "ellipsis.circle"
        }
    }

    var subtitle: String {
        switch self {
        case .home:
            return "Validated daily surface"
        case .trends:
            return "Future analytics shell"
        case .workouts:
            return "Session history"
        case .calendar:
            return "Monthly consistency"
        case .body:
            return "Measurements and trends"
        case .more:
            return "Settings and access"
        }
    }

    var sectionStateTitle: String {
        switch self {
        case .home:
            return "Live"
        case .trends:
            return "Scaffold"
        case .workouts, .calendar, .body, .more:
            return "Planned"
        }
    }

    var sectionStateVariant: DSMetricPill.Variant {
        switch self {
        case .home:
            return .success
        case .trends:
            return .info
        case .workouts, .calendar, .body, .more:
            return .neutral
        }
    }

    var isHome: Bool {
        self == .home
    }

    var isImplemented: Bool {
        switch self {
        case .home:
            return true
        case .trends, .workouts, .calendar, .body, .more:
            return false
        }
    }

    var placeholderHeadline: String {
        switch self {
        case .home:
            return "Validated Home surface"
        case .trends:
            return "Trends foundation"
        case .workouts:
            return "Workout history foundation"
        case .calendar:
            return "Calendar foundation"
        case .body:
            return "Body foundation"
        case .more:
            return "Product controls foundation"
        }
    }

    var placeholderBody: String {
        switch self {
        case .home:
            return "Home remains the validated daily surface and continues to live in TrainingLoadScreen."
        case .trends:
            return "This section is reserved for the future premium hero chart and supporting trend surfaces."
        case .workouts:
            return "This section will surface workout history, filters, and workout detail without changing Home."
        case .calendar:
            return "This section will show monthly consistency and day-level access to past sessions."
        case .body:
            return "This section will cover weight, body measurements, and future manual entry flows."
        case .more:
            return "This section will hold settings, permissions, calibration, privacy, and profile controls."
        }
    }

    var placeholderBullets: [String] {
        switch self {
        case .home:
            return [
                "Readiness stays validated.",
                "Drivers and recommended today stay in place.",
                "Load trend remains the current load-domain host."
            ]
        case .trends:
            return [
                "Hero chart space is reserved.",
                "Load-domain analytics will land here next.",
                "No charts are implemented in Phase 6.0."
            ]
        case .workouts:
            return [
                "Session summaries will land here.",
                "Filters will stay fast and predictable.",
                "Detail screens will remain workout-first."
            ]
        case .calendar:
            return [
                "Monthly consistency will be visible here.",
                "Day drill-down will map to existing workout data.",
                "Navigation should stay lightweight."
            ]
        case .body:
            return [
                "Weight trends will live here.",
                "Body measurements will follow.",
                "Manual entry can be added later."
            ]
        case .more:
            return [
                "Permissions and calibration belong here.",
                "Language and privacy controls belong here.",
                "Profile-level settings stay separate from Home."
            ]
        }
    }

    var accessibilityLabel: String {
        "\(title), \(subtitle)"
    }
}

