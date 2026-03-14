import Foundation

struct HealthKitClientUnsupported: HealthKitClient {
    func requestAuthorization() async throws -> Bool {
        throw HealthKitClientError.unsupported
    }

    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }

    func fetchSleepSessions(since: Date?) async throws -> [HealthKitSleepSessionDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }

    func fetchRecoverySignals(since: Date?) async throws -> [HealthKitRecoverySignalDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }
}
