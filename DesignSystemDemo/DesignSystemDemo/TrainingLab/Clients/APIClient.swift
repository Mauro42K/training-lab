import Foundation

protocol APIClient: Sendable {
    func ingestWorkouts(idempotencyKey: String, payload: WorkoutIngestDTO) async throws -> IngestResponseDTO
    func fetchWorkouts(from: Date, to: Date, sport: SportType?) async throws -> [WorkoutDTO]
    func fetchDaily(from: Date, to: Date) async throws -> [DailyItemDTO]
    func fetchTrainingLoad(days: Int, sport: TrainingLoadSportFilter) async throws -> TrainingLoadSummaryDTO
}

enum APIClientError: Error, LocalizedError {
    case invalidURL
    case unauthorized
    case conflict
    case unexpectedStatus(Int)
    case encodingFailed

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            "Invalid API URL"
        case .unauthorized:
            "Unauthorized"
        case .conflict:
            "Conflict"
        case let .unexpectedStatus(code):
            "Unexpected status code: \(code)"
        case .encodingFailed:
            "Failed to encode request"
        }
    }
}
