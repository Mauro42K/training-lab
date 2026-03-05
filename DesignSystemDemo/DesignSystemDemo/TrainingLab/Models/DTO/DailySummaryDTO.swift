import Foundation

struct DailyItemDTO: Codable, Equatable, Sendable {
    let date: Date
    let workoutsCount: Int
    let durationSecTotal: Int
    let distanceMTotal: Double?
    let energyKcalTotal: Double?
}

struct DailySummaryDTO: Codable, Equatable, Sendable {
    let items: [DailyItemDTO]
}
