import Foundation

protocol HealthKitClient: Sendable {
    func requestAuthorization() async throws -> Bool
    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO]
}

enum HealthKitClientError: Error, LocalizedError {
    case unsupported

    var errorDescription: String? {
        switch self {
        case .unsupported:
            "HealthKit unsupported"
        }
    }
}
