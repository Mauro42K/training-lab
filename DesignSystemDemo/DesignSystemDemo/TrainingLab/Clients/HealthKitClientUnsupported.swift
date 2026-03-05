import Foundation

struct HealthKitClientUnsupported: HealthKitClient {
    func requestAuthorization() async throws -> Bool {
        throw HealthKitClientError.unsupported
    }

    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }
}
