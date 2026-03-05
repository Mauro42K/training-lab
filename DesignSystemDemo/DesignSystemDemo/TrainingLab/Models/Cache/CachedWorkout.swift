import Foundation
import SwiftData

@Model
final class CachedWorkout {
    var userId: String?
    var uuid: String
    var sportRaw: String
    var start: Date
    var end: Date
    var durationSec: Int
    var distanceM: Double?
    var energyKcal: Double?
    var updatedAt: Date

    init(
        userId: String? = nil,
        uuid: String,
        sportRaw: String,
        start: Date,
        end: Date,
        durationSec: Int,
        distanceM: Double? = nil,
        energyKcal: Double? = nil,
        updatedAt: Date = Date()
    ) {
        self.userId = userId
        self.uuid = uuid
        self.sportRaw = sportRaw
        self.start = start
        self.end = end
        self.durationSec = durationSec
        self.distanceM = distanceM
        self.energyKcal = energyKcal
        self.updatedAt = updatedAt
    }
}
