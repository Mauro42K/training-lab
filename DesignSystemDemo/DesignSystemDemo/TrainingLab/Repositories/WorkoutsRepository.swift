import Foundation
import SwiftData

@MainActor
final class WorkoutsRepository {
    private let apiClient: any APIClient
    private let modelContext: ModelContext

    init(apiClient: any APIClient, modelContext: ModelContext) {
        self.apiClient = apiClient
        self.modelContext = modelContext
    }

    func getWorkouts(from: Date, to: Date, sport: SportType?) async throws -> [WorkoutDTO] {
        do {
            let remote = try await apiClient.fetchWorkouts(from: from, to: to, sport: sport)
            do {
                try replaceCache(from: from, to: to, with: remote)
            } catch {
                throw RepositoryError.cacheWriteFailed(underlying: error)
            }
            return remote
        } catch {
            let cached = try fetchCached(from: from, to: to, sport: sport)
            if cached.isEmpty {
                throw RepositoryError.networkAndNoCache(underlying: error)
            }
            return cached
        }
    }

    private func replaceCache(from: Date, to: Date, with workouts: [WorkoutDTO]) throws {
        let predicate = #Predicate<CachedWorkout> { item in
            item.start >= from && item.start <= to
        }
        let descriptor = FetchDescriptor<CachedWorkout>(predicate: predicate)
        let existing = try modelContext.fetch(descriptor)
        for item in existing {
            modelContext.delete(item)
        }

        for workout in workouts {
            let cached = CachedWorkout(
                uuid: workout.uuid,
                sportRaw: workout.sport.rawValue,
                start: workout.start,
                end: workout.end,
                durationSec: workout.durationSec,
                distanceM: workout.distanceM,
                energyKcal: workout.energyKcal,
                updatedAt: Date()
            )
            modelContext.insert(cached)
        }

        try modelContext.save()
    }

    private func fetchCached(from: Date, to: Date, sport: SportType?) throws -> [WorkoutDTO] {
        let predicate = #Predicate<CachedWorkout> { item in
            item.start >= from && item.start <= to
        }
        let descriptor = FetchDescriptor<CachedWorkout>(predicate: predicate, sortBy: [SortDescriptor(\CachedWorkout.start)])
        let cached = try modelContext.fetch(descriptor)

        return cached.compactMap { item in
            let sportValue = SportType(serverValue: item.sportRaw)
            if let sport, sportValue != sport {
                return nil
            }

            return WorkoutDTO(
                uuid: item.uuid,
                sport: sportValue,
                start: item.start,
                end: item.end,
                durationSec: item.durationSec,
                distanceM: item.distanceM,
                energyKcal: item.energyKcal,
                sourceBundleId: nil,
                deviceName: nil
            )
        }
    }
}
