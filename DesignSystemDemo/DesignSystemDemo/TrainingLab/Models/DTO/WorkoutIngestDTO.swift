import Foundation

struct WorkoutIngestDTO: Codable, Equatable, Sendable {
    let workouts: [WorkoutDTO]
}

struct IngestResponseDTO: Decodable, Equatable, Sendable {
    let accepted: Int
    let updated: Int
    let idempotentReplay: Bool

    init(accepted: Int = 0, updated: Int = 0, idempotentReplay: Bool = false) {
        self.accepted = accepted
        self.updated = updated
        self.idempotentReplay = idempotentReplay
    }

    private enum CodingKeys: String, CodingKey {
        case accepted
        case inserted
        case updated
        case totalReceived = "total_received"
        case idempotentReplay
        case idempotentReplaySnake = "idempotent_replay"
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

        self.init(accepted: accepted, updated: updated, idempotentReplay: idempotentReplay)
    }
}
