import SwiftUI

enum AppElevation {
    case flat
    case card
    case dropdown
    case modal

    var shadow: AppShadow? {
        switch self {
        case .flat:
            nil
        case .card:
            AppShadows.card
        case .dropdown:
            AppShadows.dropdown
        case .modal:
            AppShadows.modal
        }
    }

    var surfaceColor: Color {
        switch self {
        case .flat:
            AppColors.Background.elevated
        case .card:
            AppColors.Surface.card
        case .dropdown:
            AppColors.Surface.cardMuted
        case .modal:
            AppColors.Background.elevated
        }
    }
}
