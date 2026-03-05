import Foundation

enum SportType: String, Codable, CaseIterable, Sendable {
    case run
    case bike
    case strength
    case walk
    case other

    init(serverValue: String) {
        self = SportType(rawValue: serverValue.lowercased()) ?? .other
    }
}
