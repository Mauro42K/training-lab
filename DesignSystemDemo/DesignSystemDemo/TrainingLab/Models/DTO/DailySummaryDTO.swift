import Foundation

struct DailyItemDTO: Codable, Equatable, Sendable {
    let date: Date
    let workoutsCount: Int
    let durationSecTotal: Int
    let distanceMTotal: Double?
    let energyKcalTotal: Double?

    enum CodingKeys: String, CodingKey {
        case date
        case workoutsCount = "workouts_count"
        case durationSecTotal = "duration_sec_total"
        case distanceMTotal = "distance_m_total"
        case energyKcalTotal = "energy_kcal_total"
    }
}

struct DailySummaryDTO: Codable, Equatable, Sendable {
    let items: [DailyItemDTO]
}

enum ReadinessCompletenessStatusDTO: String, Codable, Equatable, Sendable {
    case complete
    case partial
    case insufficient
    case missing
}

enum ReadinessLabelDTO: String, Codable, Equatable, Sendable {
    case ready = "Ready"
    case moderate = "Moderate"
    case recover = "Recover"
}

enum ReadinessTraceRoleDTO: String, Codable, Equatable, Sendable {
    case primary
    case context
}

enum ReadinessTraceEffectDTO: String, Codable, Equatable, Sendable {
    case positive
    case neutral
    case negative
    case notUsed = "not_used"
}

struct ReadinessTraceInputDTO: Codable, Equatable, Sendable {
    let name: String
    let role: ReadinessTraceRoleDTO
    let present: Bool
    let baselineUsed: Bool
    let effect: ReadinessTraceEffectDTO

    enum CodingKeys: String, CodingKey {
        case name
        case role
        case present
        case baselineUsed = "baseline_used"
        case effect
    }
}

struct ReadinessSummaryDTO: Codable, Equatable, Sendable {
    let score: Int?
    let label: ReadinessLabelDTO?
    let confidence: Double
    let completenessStatus: ReadinessCompletenessStatusDTO
    let inputsPresent: [String]
    let inputsMissing: [String]
    let modelVersion: Int
    let hasEstimatedContext: Bool
    let traceSummary: [ReadinessTraceInputDTO]

    enum CodingKeys: String, CodingKey {
        case score
        case label
        case confidence
        case completenessStatus = "completeness_status"
        case inputsPresent = "inputs_present"
        case inputsMissing = "inputs_missing"
        case modelVersion = "model_version"
        case hasEstimatedContext = "has_estimated_context"
        case traceSummary = "trace_summary"
    }
}

struct CoreMetricsSummaryDTO: Codable, Equatable, Sendable {
    let sevenDayLoad: Double
    let fitness: Double
    let fatigue: Double
    let historyStatus: TrainingLoadHistoryStatus

    enum CodingKeys: String, CodingKey {
        case sevenDayLoad = "seven_day_load"
        case fitness
        case fatigue
        case historyStatus = "history_status"
    }
}

struct HomeSummaryDTO: Codable, Equatable, Sendable {
    let date: Date
    let readiness: ReadinessSummaryDTO?
    let coreMetrics: CoreMetricsSummaryDTO?

    enum CodingKeys: String, CodingKey {
        case date
        case readiness
        case coreMetrics = "core_metrics"
    }
}
