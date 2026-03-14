import Foundation

protocol HealthKitClient: Sendable {
    func requestAuthorization() async throws -> Bool
    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO]
    func fetchSleepSessions(since: Date?) async throws -> [HealthKitSleepSessionDTO]
    func fetchRecoverySignals(since: Date?) async throws -> [HealthKitRecoverySignalDTO]
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

struct HealthKitSleepSessionDTO: Equatable, Sendable {
    let uuid: String
    let start: Date
    let end: Date
    let categoryValue: String?
    let sourceBundleId: String?
    let sourceCount: Int
    let hasMixedSources: Bool
    let primaryDeviceName: String?
}

struct HealthKitRecoverySignalDTO: Equatable, Sendable {
    let uuid: String
    let signalType: RecoverySignalTypeDTO
    let measuredAt: Date
    let value: Double
    let sourceBundleId: String?
    let sourceCount: Int
    let hasMixedSources: Bool
    let primaryDeviceName: String?
}
