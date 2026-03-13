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

    init(
        items: [TrainingLoadItemDTO],
        historyStatus: TrainingLoadHistoryStatus,
        semanticState: TrainingLoadSemanticState?,
        latestLoad: Double,
        latestCapacity: Double
    ) {
        self.items = items
        self.historyStatus = historyStatus
        self.semanticState = semanticState
        self.latestLoad = latestLoad
        self.latestCapacity = latestCapacity
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let payloadItems = try container.decode([DecodedTrainingLoadItem].self, forKey: .items)
        let capacitySeries = if payloadItems.contains(where: { $0.capacity != nil }) {
            payloadItems.map { $0.capacity ?? 0 }
        } else {
            Self.calculateEMASeries(
                payloadItems.map(\.load),
                windowDays: 42
            )
        }

        let items = zip(payloadItems, capacitySeries).map { payload, capacity in
            TrainingLoadItemDTO(
                date: payload.date,
                load: payload.load,
                capacity: capacity,
                trimp: payload.trimp ?? payload.load
            )
        }

        let historyStatus = try container.decodeIfPresent(TrainingLoadHistoryStatus.self, forKey: .historyStatus)
            ?? Self.derivedHistoryStatus(from: items)
        let latestLoad = try container.decodeIfPresent(Double.self, forKey: .latestLoad)
            ?? items.last?.load
            ?? 0
        let latestCapacity = try container.decodeIfPresent(Double.self, forKey: .latestCapacity)
            ?? items.last?.capacity
            ?? 0
        let semanticState = try container.decodeIfPresent(TrainingLoadSemanticState.self, forKey: .semanticState)
            ?? Self.derivedSemanticState(
                from: items,
                historyStatus: historyStatus,
                latestCapacity: latestCapacity
            )

        self.init(
            items: items,
            historyStatus: historyStatus,
            semanticState: semanticState,
            latestLoad: latestLoad,
            latestCapacity: latestCapacity
        )
    }

    private struct DecodedTrainingLoadItem: Decodable {
        let date: Date
        let load: Double
        let capacity: Double?
        let trimp: Double?

        enum CodingKeys: String, CodingKey {
            case date
            case load
            case capacity
            case trimp
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            date = try container.decode(Date.self, forKey: .date)
            load = try container.decodeIfPresent(Double.self, forKey: .load)
                ?? container.decode(Double.self, forKey: .trimp)
            capacity = try container.decodeIfPresent(Double.self, forKey: .capacity)
            trimp = try container.decodeIfPresent(Double.self, forKey: .trimp)
        }
    }

    private static func derivedHistoryStatus(from items: [TrainingLoadItemDTO]) -> TrainingLoadHistoryStatus {
        guard let firstDate = items.first?.date, let lastDate = items.last?.date else {
            return .missing
        }

        let calendar = Calendar.current
        let firstDay = calendar.startOfDay(for: firstDate)
        let lastDay = calendar.startOfDay(for: lastDate)
        let coverageDays = max(
            (calendar.dateComponents([.day], from: firstDay, to: lastDay).day ?? (items.count - 1)) + 1,
            items.count
        )

        switch coverageDays {
        case 42...:
            return .available
        case 14...41:
            return .partial
        case 1...13:
            return .insufficientHistory
        default:
            return .missing
        }
    }

    private static func derivedSemanticState(
        from items: [TrainingLoadItemDTO],
        historyStatus: TrainingLoadHistoryStatus,
        latestCapacity: Double
    ) -> TrainingLoadSemanticState? {
        guard historyStatus != .missing, historyStatus != .insufficientHistory, latestCapacity > 0 else {
            return nil
        }

        let fatigueSeries = calculateEMASeries(items.map(\.load), windowDays: 7)
        let latestFatigue = fatigueSeries.last ?? 0
        let ratio = latestFatigue / latestCapacity

        if ratio < 0.85 {
            return .belowCapacity
        }
        if ratio <= 1.0 {
            return .withinRange
        }
        if ratio <= 1.15 {
            return .nearLimit
        }
        return .aboveCapacity
    }

    private static func calculateEMASeries(_ values: [Double], windowDays: Int) -> [Double] {
        guard !values.isEmpty else {
            return []
        }

        let alpha = 2 / (Double(windowDays) + 1)
        var series: [Double] = []
        var currentEMA = 0.0

        for value in values {
            currentEMA = currentEMA + alpha * (value - currentEMA)
            series.append(currentEMA)
        }

        return series
    }
}
