import Foundation

struct WorkoutDTO: Codable, Equatable, Sendable {
    let uuid: String
    let sport: SportType
    let start: Date
    let end: Date
    let durationSec: Int
    let avgHRBpm: Double?
    let distanceM: Double?
    let energyKcal: Double?
    let sourceBundleId: String?
    let deviceName: String?
    let isDeleted: Bool

    enum CodingKeys: String, CodingKey {
        case uuid = "healthkit_workout_uuid"
        case sport
        case start
        case end
        case durationSec = "duration_sec"
        case avgHRBpm = "avg_hr_bpm"
        case distanceM = "distance_m"
        case energyKcal = "energy_kcal"
        case sourceBundleId = "source_bundle_id"
        case deviceName = "device_name"
        case isDeleted = "is_deleted"
    }

    init(
        uuid: String,
        sport: SportType,
        start: Date,
        end: Date,
        durationSec: Int,
        avgHRBpm: Double? = nil,
        distanceM: Double? = nil,
        energyKcal: Double? = nil,
        sourceBundleId: String? = nil,
        deviceName: String? = nil,
        isDeleted: Bool = false
    ) {
        self.uuid = uuid
        self.sport = sport
        self.start = start
        self.end = end
        self.durationSec = durationSec
        self.avgHRBpm = avgHRBpm
        self.distanceM = distanceM
        self.energyKcal = energyKcal
        self.sourceBundleId = sourceBundleId
        self.deviceName = deviceName
        self.isDeleted = isDeleted
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        uuid = try container.decode(String.self, forKey: .uuid)
        sport = try container.decode(SportType.self, forKey: .sport)
        start = try container.decode(Date.self, forKey: .start)
        end = try container.decode(Date.self, forKey: .end)
        durationSec = try container.decode(Int.self, forKey: .durationSec)
        avgHRBpm = try container.decodeIfPresent(Double.self, forKey: .avgHRBpm)
        distanceM = try container.decodeIfPresent(Double.self, forKey: .distanceM)
        energyKcal = try container.decodeIfPresent(Double.self, forKey: .energyKcal)
        sourceBundleId = try container.decodeIfPresent(String.self, forKey: .sourceBundleId)
        deviceName = try container.decodeIfPresent(String.self, forKey: .deviceName)
        isDeleted = try container.decodeIfPresent(Bool.self, forKey: .isDeleted) ?? false
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(uuid, forKey: .uuid)
        try container.encode(sport, forKey: .sport)
        try container.encode(start, forKey: .start)
        try container.encode(end, forKey: .end)
        try container.encode(durationSec, forKey: .durationSec)
        try container.encodeIfPresent(avgHRBpm, forKey: .avgHRBpm)
        try container.encodeIfPresent(distanceM, forKey: .distanceM)
        try container.encodeIfPresent(energyKcal, forKey: .energyKcal)
        try container.encodeIfPresent(sourceBundleId, forKey: .sourceBundleId)
        try container.encodeIfPresent(deviceName, forKey: .deviceName)
        try container.encode(isDeleted, forKey: .isDeleted)
    }
}

struct WorkoutsSummaryDTO: Codable, Equatable, Sendable {
    let items: [WorkoutDTO]
}
