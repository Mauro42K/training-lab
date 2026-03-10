import Foundation

#if canImport(HealthKit)
import HealthKit
import OSLog

struct HealthKitClientLive: HealthKitClient {
    private let healthStore = HKHealthStore()
    #if DEBUG
    private let logger = Logger(subsystem: "com.traininglab.designsystemdemo", category: "healthkit")
    #endif

    func requestAuthorization() async throws -> Bool {
        guard HKHealthStore.isHealthDataAvailable() else {
            #if DEBUG
            logger.error("requestAuthorization unavailable health_data=false")
            #endif
            throw HealthKitClientError.unsupported
        }

        let workoutType = HKObjectType.workoutType()
        var readTypes: Set<HKObjectType> = [workoutType]
        if let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) {
            readTypes.insert(heartRateType)
        }

        #if DEBUG
        logger.log("requestAuthorization start read_types=\(readTypes.count)")
        #endif
        return try await withCheckedThrowingContinuation { continuation in
            healthStore.requestAuthorization(toShare: [], read: readTypes) { success, error in
                if let error {
                    #if DEBUG
                    logger.error("requestAuthorization failed error=\(error.localizedDescription, privacy: .public)")
                    #endif
                    continuation.resume(throwing: error)
                    return
                }
                #if DEBUG
                logger.log("requestAuthorization result authorized=\(success)")
                #endif
                continuation.resume(returning: success)
            }
        }
    }

    func fetchWorkouts(since: Date?) async throws -> [WorkoutDTO] {
        #if DEBUG
        logger.log("fetchWorkouts start since=\(debugDateString(since), privacy: .public)")
        #endif
        let workouts = try await queryWorkouts(since: since)
        var mapped: [WorkoutDTO] = []
        mapped.reserveCapacity(workouts.count)
        for workout in workouts {
            let avgHRBpm: Double?
            do {
                avgHRBpm = try await averageHeartRateBPM(for: workout)
            } catch {
                #if DEBUG
                logger.error(
                    "averageHeartRateBPM fallback_nil uuid=\(workout.uuid.uuidString.lowercased(), privacy: .public) error=\(error.localizedDescription, privacy: .public)"
                )
                #endif
                avgHRBpm = nil
            }
            mapped.append(
                WorkoutDTO(
                    uuid: workout.uuid.uuidString.lowercased(),
                    sport: mapSportType(workout.workoutActivityType),
                    start: workout.startDate,
                    end: workout.endDate,
                    durationSec: max(Int(workout.duration.rounded()), 0),
                    avgHRBpm: avgHRBpm,
                    distanceM: workout.totalDistance?.doubleValue(for: .meter()),
                    energyKcal: activeEnergyKcal(for: workout),
                    sourceBundleId: workout.sourceRevision.source.bundleIdentifier,
                    deviceName: workout.device?.name,
                    isDeleted: false
                )
            )
        }

        // Keep payload deterministic to guarantee stable idempotency keys.
        let sorted = mapped.sorted {
            if $0.start == $1.start {
                return $0.uuid < $1.uuid
            }
            return $0.start < $1.start
        }
        #if DEBUG
        logFetchSummary(workouts: sorted)
        #endif
        return sorted
    }

    private func queryWorkouts(since: Date?) async throws -> [HKWorkout] {
        let workoutType = HKObjectType.workoutType()
        let predicate: NSPredicate?
        if let since {
            predicate = HKQuery.predicateForSamples(
                withStart: since,
                end: nil,
                options: [.strictEndDate]
            )
        } else {
            predicate = nil
        }

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: true)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: workoutType,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: [sort]
            ) { _, samples, error in
                if let error {
                    if isNoDataError(error) {
                        #if DEBUG
                        logger.log("queryWorkouts no_data predicate_since=\(debugDateString(since), privacy: .public)")
                        #endif
                        continuation.resume(returning: [])
                        return
                    }
                    #if DEBUG
                    logger.error("queryWorkouts failed error=\(error.localizedDescription, privacy: .public)")
                    #endif
                    continuation.resume(throwing: error)
                    return
                }
                let workouts = (samples as? [HKWorkout]) ?? []
                continuation.resume(returning: workouts)
            }
            healthStore.execute(query)
        }
    }

    private func mapSportType(_ activityType: HKWorkoutActivityType) -> SportType {
        switch activityType {
        case .running:
            return .run
        case .cycling, .handCycling:
            return .bike
        case .traditionalStrengthTraining, .functionalStrengthTraining, .coreTraining:
            return .strength
        case .walking, .hiking:
            return .walk
        default:
            return .other
        }
    }

    private func averageHeartRateBPM(for workout: HKWorkout) async throws -> Double? {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return nil
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: workout.startDate,
            end: workout.endDate,
            options: [.strictStartDate, .strictEndDate]
        )

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: heartRateType,
                quantitySamplePredicate: predicate,
                options: [.discreteAverage]
            ) { _, result, error in
                if let error {
                    if isNoDataError(error) {
                        #if DEBUG
                        logger.log("averageHeartRateBPM no_data uuid=\(workout.uuid.uuidString.lowercased(), privacy: .public)")
                        #endif
                        continuation.resume(returning: nil)
                        return
                    }
                    #if DEBUG
                    logger.error(
                        "averageHeartRateBPM failed uuid=\(workout.uuid.uuidString.lowercased(), privacy: .public) error=\(error.localizedDescription, privacy: .public)"
                    )
                    #endif
                    continuation.resume(throwing: error)
                    return
                }

                let bpm = result?
                    .averageQuantity()?
                    .doubleValue(for: HKUnit.count().unitDivided(by: HKUnit.minute()))
                continuation.resume(returning: sanitizedAverageHeartRateBPM(bpm, workoutUUID: workout.uuid))
            }
            healthStore.execute(query)
        }
    }

    private func activeEnergyKcal(for workout: HKWorkout) -> Double? {
        guard let activeEnergyType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else {
            return nil
        }

        return workout
            .statistics(for: activeEnergyType)?
            .sumQuantity()?
            .doubleValue(for: .kilocalorie())
    }

    private func sanitizedAverageHeartRateBPM(_ bpm: Double?, workoutUUID: UUID) -> Double? {
        guard let bpm else {
            return nil
        }

        guard bpm.isFinite, (20.0...260.0).contains(bpm) else {
            #if DEBUG
            let formattedBPM = String(format: "%.2f", bpm)
            logger.log(
                "averageHeartRateBPM discard_invalid uuid=\(workoutUUID.uuidString.lowercased(), privacy: .public) bpm=\(formattedBPM, privacy: .public)"
            )
            #endif
            return nil
        }

        return bpm
    }

    #if DEBUG
    private func logFetchSummary(workouts: [WorkoutDTO]) {
        guard !workouts.isEmpty else {
            logger.log("fetchWorkouts finish count=0 date_range=none sport_counts={} source_counts={} first_uuids=[]")
            return
        }

        let sportCounts = Dictionary(grouping: workouts, by: { $0.sport.rawValue })
            .mapValues(\.count)
        let sourceCounts = Dictionary(grouping: workouts, by: { ($0.sourceBundleId?.isEmpty == false ? $0.sourceBundleId! : "unknown") })
            .mapValues(\.count)
        let firstUUIDs = workouts.prefix(5).map(\.uuid)
        let fixtureUUIDs = workouts.filter { looksLikeFixtureUUID($0.uuid) }.map(\.uuid)
        let start = workouts.first?.start
        let end = workouts.last?.end

        logger.log(
            "fetchWorkouts finish count=\(workouts.count) date_range=\(debugDateString(start), privacy: .public)...\(debugDateString(end), privacy: .public) sport_counts=\(sportCounts.debugDescription, privacy: .public) source_counts=\(sourceCounts.debugDescription, privacy: .public) first_uuids=\(firstUUIDs.debugDescription, privacy: .public) fixture_like_uuids=\(fixtureUUIDs.prefix(5).debugDescription, privacy: .public)"
        )
    }

    private func debugDateString(_ date: Date?) -> String {
        guard let date else { return "nil" }
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: date)
    }

    private func looksLikeFixtureUUID(_ uuid: String) -> Bool {
        let normalized = uuid.lowercased()
        return normalized == "00000000-0000-0000-0000-000000000001"
            || normalized == "11111111-1111-1111-1111-111111111111"
            || Set(normalized.replacingOccurrences(of: "-", with: "")).count <= 1
    }
    #endif

    private func isNoDataError(_ error: Error) -> Bool {
        if let hkError = error as? HKError, hkError.code == .errorNoData {
            return true
        }

        let nsError = error as NSError
        return nsError.domain == HKError.errorDomain
            && nsError.code == HKError.Code.errorNoData.rawValue
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
