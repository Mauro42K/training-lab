import Foundation

enum TrainingLoadHistoryStatus: String, Codable, Equatable, Sendable {
    case available
    case partial
    case insufficientHistory = "insufficient_history"
    case missing
}

enum TrainingLoadSemanticState: String, Codable, Equatable, Sendable {
    case belowCapacity = "below_capacity"
    case withinRange = "within_range"
    case nearLimit = "near_limit"
    case aboveCapacity = "above_capacity"
}

struct TrainingLoadItemDTO: Codable, Equatable, Sendable, Identifiable {
    let date: Date
    let load: Double
    let capacity: Double
    let trimp: Double

    var id: Date { date }

    enum CodingKeys: String, CodingKey {
        case date
        case load
        case capacity
        case trimp
    }

    init(date: Date, load: Double, capacity: Double, trimp: Double? = nil) {
        self.date = date
        self.load = load
        self.capacity = capacity
        self.trimp = trimp ?? load
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let date = try container.decode(Date.self, forKey: .date)
        let load = try container.decodeIfPresent(Double.self, forKey: .load)
            ?? container.decode(Double.self, forKey: .trimp)
        let capacity = try container.decodeIfPresent(Double.self, forKey: .capacity) ?? 0
        let trimp = try container.decodeIfPresent(Double.self, forKey: .trimp) ?? load
        self.init(date: date, load: load, capacity: capacity, trimp: trimp)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(date, forKey: .date)
        try container.encode(load, forKey: .load)
        try container.encode(capacity, forKey: .capacity)
        try container.encode(trimp, forKey: .trimp)
    }
}

struct TrainingLoadSummaryDTO: Codable, Equatable, Sendable {
    let items: [TrainingLoadItemDTO]
    let historyStatus: TrainingLoadHistoryStatus
    let semanticState: TrainingLoadSemanticState?
    let latestLoad: Double
    let latestCapacity: Double

    enum CodingKeys: String, CodingKey {
        case items
        case historyStatus = "history_status"
        case semanticState = "semantic_state"
        case latestLoad = "latest_load"
        case latestCapacity = "latest_capacity"
    }
}
