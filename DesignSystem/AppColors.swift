import SwiftUI

#if canImport(UIKit)
import UIKit
#elseif canImport(AppKit)
import AppKit
#endif

enum AppColors {
    enum Background {
        static let primary = Color.dynamic(darkHex: 0x0B0B0D, lightHex: 0xF5F5F7)
        static let elevated = Color.dynamic(darkHex: 0x111115, lightHex: 0xFFFFFF)
    }

    enum Surface {
        static let card = Color.dynamic(darkHex: 0x151518, lightHex: 0xFFFFFF)
        static let cardMuted = Color.dynamic(darkHex: 0x1C1C21, lightHex: 0xF0F1F5)
    }

    enum Text {
        static let primary = Color.dynamic(darkHex: 0xFFFFFF, lightHex: 0x111115)
        static let secondary = Color.dynamic(darkHex: 0xA0A0A6, lightHex: 0x61616A)
        static let inverse = Color.dynamic(darkHex: 0x111115, lightHex: 0xFFFFFF)
    }

    enum Stroke {
        static let subtle = Color.dynamic(darkHex: 0xFFFFFF, lightHex: 0x111115, darkOpacity: 0.10, lightOpacity: 0.08)
        static let strong = Color.dynamic(darkHex: 0xFFFFFF, lightHex: 0x111115, darkOpacity: 0.20, lightOpacity: 0.16)
    }

    enum Accent {
        static let blue = Color.dynamic(darkHex: 0x3A7BFF, lightHex: 0x2F6DE8)
        static let green = Color.dynamic(darkHex: 0x3DDC84, lightHex: 0x2FC46E)
        static let amber = Color.dynamic(darkHex: 0xF4C542, lightHex: 0xD6A11F)
        static let orange = Color.dynamic(darkHex: 0xFF8A3D, lightHex: 0xE9782F)
        static let coral = Color.dynamic(darkHex: 0xFF6B62, lightHex: 0xE1574D)
        static let red = Color.dynamic(darkHex: 0xFF5C5C, lightHex: 0xE14949)
        static let purple = Color.dynamic(darkHex: 0x8B7CFF, lightHex: 0x7666E8)
    }
}

private extension Color {
    static func dynamic(
        darkHex: UInt32,
        lightHex: UInt32,
        darkOpacity: Double = 1,
        lightOpacity: Double = 1
    ) -> Color {
        #if canImport(UIKit)
        Color(
            UIColor { traitCollection in
                if traitCollection.userInterfaceStyle == .dark {
                    return UIColor(hex: darkHex, opacity: darkOpacity)
                }
                return UIColor(hex: lightHex, opacity: lightOpacity)
            }
        )
        #elseif canImport(AppKit)
        Color(
            NSColor(name: nil) { appearance in
                let isDark = appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
                if isDark {
                    return NSColor(hex: darkHex, opacity: darkOpacity)
                }
                return NSColor(hex: lightHex, opacity: lightOpacity)
            }
        )
        #else
        Color.white
        #endif
    }
}

#if canImport(UIKit)
private extension UIColor {
    convenience init(hex: UInt32, opacity: Double) {
        let red = CGFloat((hex >> 16) & 0xFF) / 255
        let green = CGFloat((hex >> 8) & 0xFF) / 255
        let blue = CGFloat(hex & 0xFF) / 255
        self.init(red: red, green: green, blue: blue, alpha: opacity)
    }
}
#elseif canImport(AppKit)
private extension NSColor {
    convenience init(hex: UInt32, opacity: Double) {
        let red = CGFloat((hex >> 16) & 0xFF) / 255
        let green = CGFloat((hex >> 8) & 0xFF) / 255
        let blue = CGFloat(hex & 0xFF) / 255
        self.init(red: red, green: green, blue: blue, alpha: opacity)
    }
}
#endif
