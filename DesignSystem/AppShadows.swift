import SwiftUI

struct AppShadow: Equatable {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

enum AppShadows {
    // Figma: Shadow/Card (0, 2, 8, #00000033)
    static let card = AppShadow(color: Color.black.opacity(0.20), radius: 8, x: 0, y: 2)

    // Figma: Shadow/Dropdown (0, 4, 16, #00000040)
    static let dropdown = AppShadow(color: Color.black.opacity(0.25), radius: 16, x: 0, y: 4)

    // Figma: Shadow/Modal (0, 8, 32, #0000004D)
    static let modal = AppShadow(color: Color.black.opacity(0.30), radius: 32, x: 0, y: 8)
}

extension View {
    @ViewBuilder
    func appShadow(_ shadow: AppShadow?) -> some View {
        if let shadow {
            self.shadow(color: shadow.color, radius: shadow.radius, x: shadow.x, y: shadow.y)
        } else {
            self
        }
    }
}
