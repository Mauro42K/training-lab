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
