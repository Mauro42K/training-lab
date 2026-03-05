import Foundation

enum RepositoryError: Error, LocalizedError {
    case networkAndNoCache(underlying: Error)
    case cacheWriteFailed(underlying: Error)

    var errorDescription: String? {
        switch self {
        case let .networkAndNoCache(underlying):
            "Network failed and no cache available: \(underlying.localizedDescription)"
        case let .cacheWriteFailed(underlying):
            "Cache write failed: \(underlying.localizedDescription)"
        }
    }
}
