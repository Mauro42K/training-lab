import Foundation
import SwiftData

@Model
final class CachedDailySummary {
    var date: Date
    var workoutsCount: Int
    var durationSecTotal: Int
    var distanceMTotal: Double?
    var energyKcalTotal: Double?
    var updatedAt: Date

    init(
        date: Date,
        workoutsCount: Int,
        durationSecTotal: Int,
        distanceMTotal: Double? = nil,
        energyKcalTotal: Double? = nil,
        updatedAt: Date = Date()
    ) {
        self.date = date
        self.workoutsCount = workoutsCount
        self.durationSecTotal = durationSecTotal
        self.distanceMTotal = distanceMTotal
        self.energyKcalTotal = energyKcalTotal
        self.updatedAt = updatedAt
    }
}
