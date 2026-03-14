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

        var readTypes: Set<HKObjectType> = [HKObjectType.workoutType()]
        if let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) {
            readTypes.insert(heartRateType)
        }
        if let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) {
            readTypes.insert(sleepType)
        }
        if let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) {
            readTypes.insert(hrvType)
        }
        if let restingHeartRateType = HKObjectType.quantityType(forIdentifier: .restingHeartRate) {
            readTypes.insert(restingHeartRateType)
        }

        #if DEBUG
        let requestStatus = try? await authorizationRequestStatus(readTypes: readTypes)
        logger.log(
            "requestAuthorization start read_types=\(readTypes.count) request_status=\(requestStatus ?? "unknown", privacy: .public)"
        )
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
        let queryUpperBound = Date()
        #if DEBUG
        logger.log(
            "fetchWorkouts start since=\(debugDateString(since), privacy: .public) until=\(debugDateString(queryUpperBound), privacy: .public)"
        )
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

    func fetchSleepSessions(since: Date?) async throws -> [HealthKitSleepSessionDTO] {
        let queryUpperBound = Date()
        #if DEBUG
        logger.log(
            "fetchSleepSessions start since=\(debugDateString(since), privacy: .public) until=\(debugDateString(queryUpperBound), privacy: .public)"
        )
        #endif
        do {
            let samples = try await querySleepSamples(since: since)
            let sessions = normalizedSleepSessionsForIngest(samples.map(mapSleepSample))
            #if DEBUG
            logger.log(
                "fetchSleepSessions finish count=\(sessions.count) latest_end=\(debugDateString(sessions.last?.end), privacy: .public)"
            )
            #endif
            return sessions
        } catch {
            #if DEBUG
            logger.error("fetchSleepSessions fallback_empty error=\(error.localizedDescription, privacy: .public)")
            #endif
            return []
        }
    }

    func fetchRecoverySignals(since: Date?) async throws -> [HealthKitRecoverySignalDTO] {
        let queryUpperBound = Date()
        #if DEBUG
        logger.log(
            "fetchRecoverySignals start since=\(debugDateString(since), privacy: .public) until=\(debugDateString(queryUpperBound), privacy: .public)"
        )
        #endif
        async let hrvSignals = fetchRecoverySignalsIfAvailable(
            identifier: .heartRateVariabilitySDNN,
            signalType: .hrvSDNN,
            unit: HKUnit.secondUnit(with: .milli),
            since: since
        )
        async let restingHeartRateSignals = fetchRecoverySignalsIfAvailable(
            identifier: .restingHeartRate,
            signalType: .restingHR,
            unit: HKUnit.count().unitDivided(by: .minute()),
            since: since
        )

        let hrv = try await hrvSignals
        let resting = try await restingHeartRateSignals
        let combined = normalizedRecoverySignalsForIngest(hrv + resting)
        #if DEBUG
        logger.log(
            "fetchRecoverySignals finish hrv_count=\(hrv.count) resting_hr_count=\(resting.count) total_count=\(combined.count) latest_measured_at=\(debugDateString(combined.last?.measuredAt), privacy: .public)"
        )
        #endif
        return combined
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

    private func querySleepSamples(since: Date?) async throws -> [HKCategorySample] {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else {
            return []
        }

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
                sampleType: sleepType,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: [sort]
            ) { _, samples, error in
                if let error {
                    if isNoDataError(error) {
                        continuation.resume(returning: [])
                        return
                    }
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: (samples as? [HKCategorySample]) ?? [])
            }
            healthStore.execute(query)
        }
    }

    private func fetchRecoverySignalsIfAvailable(
        identifier: HKQuantityTypeIdentifier,
        signalType: RecoverySignalTypeDTO,
        unit: HKUnit,
        since: Date?
    ) async throws -> [HealthKitRecoverySignalDTO] {
        do {
            let samples = try await queryRecoveryQuantitySamples(identifier: identifier, since: since)
            return samples.compactMap { sample in
                let value = sample.quantity.doubleValue(for: unit)
                guard value.isFinite else {
                    return nil
                }
                return HealthKitRecoverySignalDTO(
                    uuid: sample.uuid.uuidString.lowercased(),
                    signalType: signalType,
                    measuredAt: sample.startDate,
                    value: value,
                    sourceBundleId: sample.sourceRevision.source.bundleIdentifier,
                    sourceCount: 1,
                    hasMixedSources: false,
                    primaryDeviceName: sample.device?.name
                )
            }
        } catch {
            #if DEBUG
            logger.error(
                "fetchRecoverySignals partial_fallback signal_type=\(signalType.rawValue, privacy: .public) error=\(error.localizedDescription, privacy: .public)"
            )
            #endif
            return []
        }
    }

    private func queryRecoveryQuantitySamples(
        identifier: HKQuantityTypeIdentifier,
        since: Date?
    ) async throws -> [HKQuantitySample] {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: identifier) else {
            return []
        }

        let predicate: NSPredicate?
        if let since {
            predicate = HKQuery.predicateForSamples(
                withStart: since,
                end: nil,
                options: [.strictStartDate]
            )
        } else {
            predicate = nil
        }
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: quantityType,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: [sort]
            ) { _, samples, error in
                if let error {
                    if isNoDataError(error) {
                        continuation.resume(returning: [])
                        return
                    }
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: (samples as? [HKQuantitySample]) ?? [])
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

    private func mapSleepSample(_ sample: HKCategorySample) -> HealthKitSleepSessionDTO {
        HealthKitSleepSessionDTO(
            uuid: sample.uuid.uuidString.lowercased(),
            start: sample.startDate,
            end: sample.endDate,
            categoryValue: String(sample.value),
            sourceBundleId: sample.sourceRevision.source.bundleIdentifier,
            sourceCount: 1,
            hasMixedSources: false,
            primaryDeviceName: sample.device?.name
        )
    }

    private func normalizedSleepSessionsForIngest(_ sessions: [HealthKitSleepSessionDTO]) -> [HealthKitSleepSessionDTO] {
        var byUUID: [String: HealthKitSleepSessionDTO] = [:]
        byUUID.reserveCapacity(sessions.count)

        for session in sessions {
            guard session.end >= session.start else {
                continue
            }
            if let existing = byUUID[session.uuid], existing.end >= session.end {
                continue
            }
            byUUID[session.uuid] = session
        }

        return byUUID.values.sorted {
            if $0.start == $1.start {
                return $0.uuid < $1.uuid
            }
            return $0.start < $1.start
        }
    }

    private func normalizedRecoverySignalsForIngest(_ signals: [HealthKitRecoverySignalDTO]) -> [HealthKitRecoverySignalDTO] {
        var byUUID: [String: HealthKitRecoverySignalDTO] = [:]
        byUUID.reserveCapacity(signals.count)

        for signal in signals {
            if let existing = byUUID[signal.uuid], existing.measuredAt >= signal.measuredAt {
                continue
            }
            byUUID[signal.uuid] = signal
        }

        return byUUID.values.sorted {
            if $0.measuredAt == $1.measuredAt {
                return $0.uuid < $1.uuid
            }
            return $0.measuredAt < $1.measuredAt
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

    private func authorizationRequestStatus(readTypes: Set<HKObjectType>) async throws -> String {
        try await withCheckedThrowingContinuation { continuation in
            healthStore.getRequestStatusForAuthorization(toShare: [], read: readTypes) { status, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }

                let rawValue: String
                switch status {
                case .unknown:
                    rawValue = "unknown"
                case .shouldRequest:
                    rawValue = "should_request"
                case .unnecessary:
                    rawValue = "unnecessary"
                @unknown default:
                    rawValue = "unknown_default"
                }
                continuation.resume(returning: rawValue)
            }
        }
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

    func fetchSleepSessions(since: Date?) async throws -> [HealthKitSleepSessionDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }

    func fetchRecoverySignals(since: Date?) async throws -> [HealthKitRecoverySignalDTO] {
        _ = since
        throw HealthKitClientError.unsupported
    }
}
#endif
