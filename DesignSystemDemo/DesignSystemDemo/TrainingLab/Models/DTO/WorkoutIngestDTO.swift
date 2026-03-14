import Foundation

struct WorkoutIngestDTO: Codable, Equatable, Sendable {
    let workouts: [WorkoutDTO]
}

struct SleepSessionIngestItemDTO: Codable, Equatable, Sendable {
    let healthkitSleepUUID: String
    let start: Date
    let end: Date
    let categoryValue: String?
    let sourceBundleId: String?
    let sourceCount: Int
    let hasMixedSources: Bool
    let primaryDeviceName: String?

    private enum CodingKeys: String, CodingKey {
        case healthkitSleepUUID = "healthkit_sleep_uuid"
        case start
        case end
        case categoryValue = "category_value"
        case sourceBundleId = "source_bundle_id"
        case sourceCount = "source_count"
        case hasMixedSources = "has_mixed_sources"
        case primaryDeviceName = "primary_device_name"
    }
}

struct SleepSessionsIngestDTO: Codable, Equatable, Sendable {
    let timezone: String
    let sleepSessions: [SleepSessionIngestItemDTO]

    private enum CodingKeys: String, CodingKey {
        case timezone
        case sleepSessions = "sleep_sessions"
    }
}

enum RecoverySignalTypeDTO: String, Codable, Equatable, Sendable {
    case hrvSDNN = "hrv_sdnn"
    case restingHR = "resting_hr"
}

struct RecoverySignalIngestItemDTO: Codable, Equatable, Sendable {
    let healthkitSignalUUID: String
    let signalType: RecoverySignalTypeDTO
    let measuredAt: Date
    let value: Double
    let sourceBundleId: String?
    let sourceCount: Int
    let hasMixedSources: Bool
    let primaryDeviceName: String?

    private enum CodingKeys: String, CodingKey {
        case healthkitSignalUUID = "healthkit_signal_uuid"
        case signalType = "signal_type"
        case measuredAt = "measured_at"
        case value
        case sourceBundleId = "source_bundle_id"
        case sourceCount = "source_count"
        case hasMixedSources = "has_mixed_sources"
        case primaryDeviceName = "primary_device_name"
    }
}

struct RecoverySignalsIngestDTO: Codable, Equatable, Sendable {
    let timezone: String
    let recoverySignals: [RecoverySignalIngestItemDTO]

    private enum CodingKeys: String, CodingKey {
        case timezone
        case recoverySignals = "recovery_signals"
    }
}

struct IngestResponseDTO: Decodable, Equatable, Sendable {
    let accepted: Int
    let updated: Int
    let idempotentReplay: Bool
    let rebuiltDates: Int?
    let invalidatedDailyRecoveryDates: Int?
    let rebuiltDailyRecoveryRows: Int?

    init(
        accepted: Int = 0,
        updated: Int = 0,
        idempotentReplay: Bool = false,
        rebuiltDates: Int? = nil,
        invalidatedDailyRecoveryDates: Int? = nil,
        rebuiltDailyRecoveryRows: Int? = nil
    ) {
        self.accepted = accepted
        self.updated = updated
        self.idempotentReplay = idempotentReplay
        self.rebuiltDates = rebuiltDates
        self.invalidatedDailyRecoveryDates = invalidatedDailyRecoveryDates
        self.rebuiltDailyRecoveryRows = rebuiltDailyRecoveryRows
    }

    private enum CodingKeys: String, CodingKey {
        case accepted
        case inserted
        case updated
        case totalReceived = "total_received"
        case idempotentReplay
        case idempotentReplaySnake = "idempotent_replay"
        case rebuiltDates = "rebuilt_dates"
        case invalidatedDailyRecoveryDates = "invalidated_daily_recovery_dates"
        case rebuiltDailyRecoveryRows = "rebuilt_daily_recovery_rows"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let accepted = try container.decodeIfPresent(Int.self, forKey: .accepted)
            ?? container.decodeIfPresent(Int.self, forKey: .totalReceived)
            ?? container.decodeIfPresent(Int.self, forKey: .inserted)
            ?? 0
        let updated = try container.decodeIfPresent(Int.self, forKey: .updated) ?? 0
        let idempotentReplay = try container.decodeIfPresent(Bool.self, forKey: .idempotentReplay)
            ?? container.decodeIfPresent(Bool.self, forKey: .idempotentReplaySnake)
            ?? false
        let rebuiltDates = try container.decodeIfPresent(Int.self, forKey: .rebuiltDates)
        let invalidatedDailyRecoveryDates = try container.decodeIfPresent(Int.self, forKey: .invalidatedDailyRecoveryDates)
        let rebuiltDailyRecoveryRows = try container.decodeIfPresent(Int.self, forKey: .rebuiltDailyRecoveryRows)

        self.init(
            accepted: accepted,
            updated: updated,
            idempotentReplay: idempotentReplay,
            rebuiltDates: rebuiltDates,
            invalidatedDailyRecoveryDates: invalidatedDailyRecoveryDates,
            rebuiltDailyRecoveryRows: rebuiltDailyRecoveryRows
        )
    }
}
