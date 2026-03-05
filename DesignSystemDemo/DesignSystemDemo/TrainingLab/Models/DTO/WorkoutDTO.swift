import Foundation

struct WorkoutDTO: Codable, Equatable, Sendable {
    let uuid: String
    let sport: SportType
    let start: Date
    let end: Date
    let durationSec: Int
    let distanceM: Double?
    let energyKcal: Double?
    let sourceBundleId: String?
    let deviceName: String?

    init(
        uuid: String,
        sport: SportType,
        start: Date,
        end: Date,
        durationSec: Int,
        distanceM: Double? = nil,
        energyKcal: Double? = nil,
        sourceBundleId: String? = nil,
        deviceName: String? = nil
    ) {
        self.uuid = uuid
        self.sport = sport
        self.start = start
        self.end = end
        self.durationSec = durationSec
        self.distanceM = distanceM
        self.energyKcal = energyKcal
        self.sourceBundleId = sourceBundleId
        self.deviceName = deviceName
    }
}
