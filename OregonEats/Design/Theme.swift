import SwiftUI
import UIKit
import CoreText

/// Oregon's official state colors (ORS 186.010; Nick's pick, 2026-10-24), light only: navy #14305C (13.1:1 on white) for titles, tint
/// and accents; gold #F2B705 only as a fill under navy text (7.2:1; gold text on white is 1.8:1 and fails AA); Crater Lake blue
/// #1F5A96 (7.1:1) for links; marionberry plum #5A1F46 (11.0:1, the icon's ground) for hand-checked picks on the map and the title's
/// shadow; Douglas fir #2E5E4E, fills only, for the firs in the header band. No Ducks green/yellow or Beavers orange/black. The names
/// `green`/`gold`/`red` are kept from Wisconsin Eats so the shared views read the same: here `green` is navy, `gold` the state gold
/// and `red` the plum.
enum Theme {
    static let green = Color(hex: 0x14305C)      // state navy: titles, tint, primary text accents
    static let green2 = Color(hex: 0x1F5A96)     // Crater Lake blue
    static let gold = Color(hex: 0xF2B705)       // state gold: fills under navy text only
    static let goldSoft = Color(hex: 0xFCEFC2)
    static let lime = Color(hex: 0x2E5E4E)       // Douglas fir (the header's firs), fills only
    static let limeSoft = Color(hex: 0xE3EEE9)
    static let sand = Color(hex: 0xF7F3EA)
    static let red = Color(hex: 0x5A1F46)        // marionberry plum: hand-checked pins, the title shadow
    static let ink = Color(hex: 0x0E1B2E)
    static let ink2 = Color(hex: 0x26364F)
    static let muted = Color(hex: 0x556275)
    static let surface = Color.white
    static let surface2 = Color(hex: 0xF3F5F9)
    static let surface3 = Color(hex: 0xE2E8F1)
    static let rule = Color(hex: 0xDCE2EB)
    static let rule2 = Color(hex: 0xB5C1D2)
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

/// A small uppercase label: "STONE CRAB", "1 MICHELIN STAR".
struct Chip: View {
    enum Style { case gold, green, red, plain, dashed }
    let text: String
    var style: Style = .plain

    var body: some View {
        Text(text.uppercased())
            .font(.caption2.weight(.bold))
            .tracking(0.4)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .foregroundStyle(style == .green || style == .red ? Color.white : style == .dashed ? Theme.muted : style == .gold ? Theme.ink : Theme.green)
            .background {
                RoundedRectangle(cornerRadius: 5).fill(style == .gold ? Theme.goldSoft : style == .green ? Theme.green : style == .red ? Theme.red
                                                       : style == .dashed ? .clear : Theme.surface2)
            }
            .overlay {
                if style == .dashed { RoundedRectangle(cornerRadius: 5).strokeBorder(Theme.rule2, style: StrokeStyle(lineWidth: 1, dash: [3, 2])) }
            }
            .accessibilityLabel(text)
    }
}

/// Oregon Eats' lettering: the system face drawn compressed and heavy for titles and guide names (like a food-cart menu board), and the
/// system monospaced face for numbers, dates and small labels. No bundled fonts.
struct DisplayFont: ViewModifier {
    let size: CGFloat
    var weight: Font.Weight = .black
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1

    func body(content: Content) -> some View {
        content.font(.system(size: size * min(scale, 1.6), weight: weight).width(.compressed))
    }
}

/// Numbers, dates and small labels in the system monospaced face, scaled like DisplayFont.
struct MonoFont: ViewModifier {
    let size: CGFloat
    var weight: Font.Weight = .semibold
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1

    func body(content: Content) -> some View {
        content.font(.system(size: size * min(scale, 1.6), weight: weight, design: .monospaced))
    }
}

extension View {
    func displayFont(_ size: CGFloat, weight: Font.Weight = .black) -> some View {
        modifier(DisplayFont(size: size, weight: weight))
    }

    func monoFont(_ size: CGFloat, weight: Font.Weight = .semibold) -> some View {
        modifier(MonoFont(size: size, weight: weight))
    }
}

/// A Mt. Hood ridgeline with a row of firs under the Home title (2026-10-24, the leaderboard's header element): a navy band, the
/// mountain's snow-capped cone in the middle and Douglas firs along the bottom, laid flat. No map, no team marks.
struct Stripes: View {
    var height: CGFloat = 6

    var body: some View {
        ZStack(alignment: .bottom) {
            Rectangle().fill(Theme.green).frame(height: height * 0.9).frame(maxHeight: .infinity, alignment: .top)
            Mountain().fill(Theme.green)
            Snow().fill(Color.white)
            Firs().fill(Theme.lime)
        }
        .frame(height: height * 4)
        .accessibilityHidden(true)
    }

    /// Mt. Hood's cone, centered, rising from the band to the full height
    private struct Mountain: Shape {
        func path(in r: CGRect) -> Path {
            var p = Path()
            let w = min(r.width * 0.22, r.height * 6)
            p.move(to: CGPoint(x: r.midX - w / 2, y: r.maxY))
            p.addLine(to: CGPoint(x: r.midX - w * 0.07, y: r.minY + r.height * 0.06))
            p.addQuadCurve(to: CGPoint(x: r.midX + w * 0.07, y: r.minY + r.height * 0.06), control: CGPoint(x: r.midX, y: r.minY - r.height * 0.06))
            p.addLine(to: CGPoint(x: r.midX + w / 2, y: r.maxY)); p.closeSubpath()
            return p
        }
    }

    /// the snow cap: the top of the cone with a zigzag lower edge
    private struct Snow: Shape {
        func path(in r: CGRect) -> Path {
            var p = Path()
            let w = min(r.width * 0.22, r.height * 6)
            let x0 = r.midX - w * 0.07, x1 = r.midX + w * 0.07, top = r.minY + r.height * 0.06
            p.move(to: CGPoint(x: x0, y: top))
            p.addQuadCurve(to: CGPoint(x: x1, y: top), control: CGPoint(x: r.midX, y: r.minY - r.height * 0.06))
            p.addLine(to: CGPoint(x: r.midX + w * 0.12, y: r.minY + r.height * 0.30))
            p.addLine(to: CGPoint(x: r.midX + w * 0.04, y: r.minY + r.height * 0.24))
            p.addLine(to: CGPoint(x: r.midX - w * 0.02, y: r.minY + r.height * 0.34))
            p.addLine(to: CGPoint(x: r.midX - w * 0.07, y: r.minY + r.height * 0.25))
            p.addLine(to: CGPoint(x: r.midX - w * 0.12, y: r.minY + r.height * 0.30))
            p.closeSubpath()
            return p
        }
    }

    /// a row of firs along the bottom, leaving the mountain's foot clear
    private struct Firs: Shape {
        func path(in r: CGRect) -> Path {
            var p = Path()
            let h = r.height * 0.45, w = h * 0.7, step = w * 1.6
            let gap = min(r.width * 0.22, r.height * 6) * 0.55
            var x = r.minX + step * 0.2
            while x + w <= r.maxX {
                if abs(x + w / 2 - r.midX) > gap {
                    p.move(to: CGPoint(x: x, y: r.maxY)); p.addLine(to: CGPoint(x: x + w / 2, y: r.maxY - h))
                    p.addLine(to: CGPoint(x: x + w, y: r.maxY)); p.closeSubpath()
                }
                x += step
            }
            return p
        }
    }
}

extension View {
    /// An inline navigation title in the display type. UINavigationBar.appearance() didn't reach every SwiftUI bar on iOS 27
    /// (the Map title went from compressed blue to plain black after a push and pop; place titles were always plain), so the
    /// title is our own view in the bar. The navigation title is still set, for the back button and VoiceOver.
    func inlineTitle(_ title: String) -> some View {
        navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text(title).displayFont(19, weight: .heavy).foregroundStyle(Theme.green)
                        .lineLimit(1).minimumScaleFactor(0.7)
                        .accessibilityAddTraits(.isHeader)
                }
            }
    }
}
