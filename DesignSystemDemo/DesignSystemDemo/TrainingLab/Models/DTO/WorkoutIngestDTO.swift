import Foundation

struct WorkoutIngestDTO: Codable, Equatable, Sendable {
    let workouts: [WorkoutDTO]
}

struct IngestResponseDTO: Codable, Equatable, Sendable {
    let accepted: Int
    let updated: Int
    let idempotentReplay: Bool

    init(accepted: Int = 0, updated: Int = 0, idempotentReplay: Bool = false) {
        self.accepted = accepted
        self.updated = updated
        self.idempotentReplay = idempotentReplay
    }
}
