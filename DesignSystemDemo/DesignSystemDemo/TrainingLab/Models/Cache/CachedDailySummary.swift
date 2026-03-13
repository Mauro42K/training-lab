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

@Model
final class CachedTrainingLoadPoint {
    var date: Date
    var sportFilterRaw: String
    var trimp: Double
    var capacity: Double?
    var historyStatusRaw: String?
    var semanticStateRaw: String?
    var latestLoad: Double?
    var latestCapacity: Double?
    var updatedAt: Date

    init(
        date: Date,
        sportFilterRaw: String,
        trimp: Double,
        capacity: Double? = nil,
        historyStatusRaw: String? = nil,
        semanticStateRaw: String? = nil,
        latestLoad: Double? = nil,
        latestCapacity: Double? = nil,
        updatedAt: Date = Date()
    ) {
        self.date = date
        self.sportFilterRaw = sportFilterRaw
        self.trimp = trimp
        self.capacity = capacity
        self.historyStatusRaw = historyStatusRaw
        self.semanticStateRaw = semanticStateRaw
        self.latestLoad = latestLoad
        self.latestCapacity = latestCapacity
        self.updatedAt = updatedAt
    }
}
