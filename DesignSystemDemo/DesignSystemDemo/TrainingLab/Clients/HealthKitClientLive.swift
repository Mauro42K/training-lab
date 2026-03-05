import Foundation

#if canImport(HealthKit)
import HealthKit

struct HealthKitClientLive: HealthKitClient {
    private let healthStore = HKHealthStore()

    func requestAuthorization() async throws -> Bool {
        let workoutType = HKObjectType.workoutType()
        let readTypes: Set<HKObjectType> = [workoutType]

        return try await withCheckedThrowingContinuation { continuation in
            healthStore.requestAuthorization(toShare: [], read: readTypes) { success, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: success)
            }
        }
    }

    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO] {
        _ = since
        return []
    }
}
#else
struct HealthKitClientLive: HealthKitClient {
    func requestAuthorization() async throws -> Bool {
        throw HealthKitClientError.unsupported
    }

    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }
}
#endif
