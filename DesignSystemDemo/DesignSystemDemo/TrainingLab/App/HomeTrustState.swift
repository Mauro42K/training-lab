import Foundation

enum HomeTrustState: String, Equatable, Sendable {
    case complete
    case partial
    case missing
}

extension ReadinessCompletenessStatusDTO {
    var homeTrustState: HomeTrustState {
        switch self {
        case .complete:
            return .complete
        case .partial, .insufficient:
            return .partial
        case .missing:
            return .missing
        }
    }
}

extension TrainingLoadHistoryStatus {
    var homeTrustState: HomeTrustState {
        switch self {
        case .available:
            return .complete
        case .partial, .insufficientHistory:
            return .partial
        case .missing:
            return .missing
        }
    }
}
