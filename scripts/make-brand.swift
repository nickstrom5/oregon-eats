// Oregon Eats brand: the app icon (Nick's pick 2026-10-24, concept B of scripts/icon-concepts.swift: a marionberry pie slice on
// marionberry plum), in the shared Eats Ranked style (../state-prompts/ICON-STYLE.md). Usage, from or-eats/: swift scripts/make-brand.swift
// -> OregonEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png, the website's icons (docs/icon-512.png, icon-192.png,
// apple-touch-icon.png, favicon-32.png) and share image (docs/og.png).
import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func rgb(_ hex: UInt32) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 255) / 255, green: CGFloat((hex >> 8) & 255) / 255, blue: CGFloat(hex & 255) / 255, alpha: 1)
}
let PLUM: UInt32 = 0x5A1F46, NAVY: UInt32 = 0x14305C, GOLD: UInt32 = 0xF2B705, FIR: UInt32 = 0x2E5E4E

/// B: a slice of marionberry pie (Oregon's state pie), front view of the cut face with one lighter top plane: the point at the left,
/// the fluted rim at the right, crust in three tones of one material, the berry filling and three berry vents. 5 colours with the ground.
func pie(_ c: CGContext, _ s: CGFloat) {
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    func R(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect { CGRect(x: x * s, y: y * s, width: w * s, height: h * s) }
    let crust = rgb(0xC98A3E), crustTop = rgb(0xE0A95E), crustLow = rgb(0xA8622A), berry = rgb(0x7A2E62)
    let topPlane = CGMutablePath()
    topPlane.move(to: P(0.14, 0.52)); topPlane.addLine(to: P(0.80, 0.52)); topPlane.addLine(to: P(0.80, 0.67)); topPlane.closeSubpath()
    c.setFillColor(crustTop); c.addPath(topPlane); c.fillPath()
    c.setFillColor(crustLow); c.fill(R(0.14, 0.31, 0.66, 0.055))
    c.setFillColor(berry); c.fill(R(0.14, 0.365, 0.66, 0.125))
    c.setFillColor(crust); c.fill(R(0.14, 0.49, 0.66, 0.03))
    c.setFillColor(crust)
    c.addPath(CGPath(roundedRect: R(0.765, 0.31, 0.095, 0.385), cornerWidth: 0.045 * s, cornerHeight: 0.045 * s, transform: nil)); c.fillPath()
    c.setStrokeColor(berry); c.setLineWidth(0.034 * s); c.setLineCap(.round)
    for (x0, x1, y) in [(0.42, 0.50, 0.555), (0.56, 0.66, 0.565), (0.60, 0.70, 0.615)] as [(CGFloat, CGFloat, CGFloat)] {
        c.move(to: P(x0, y)); c.addLine(to: P(x1, y)); c.strokePath()
    }
}

func save(_ ctx: CGContext, _ path: String) {
    let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(d, ctx.makeImage()!, nil)
    guard CGImageDestinationFinalize(d) else { fatalError("could not write \(path)") }
    print("wrote", path)
}

func canvas(_ w: Int, _ h: Int) -> CGContext {
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setShouldAntialias(true)
    return ctx
}

func render(_ n: Int, _ path: String) {
    let ctx = canvas(n, n)
    ctx.setFillColor(rgb(PLUM)); ctx.fill(CGRect(x: 0, y: 0, width: n, height: n))
    pie(ctx, CGFloat(n))
    save(ctx, path)
}
render(1024, "OregonEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png")
try? FileManager.default.createDirectory(atPath: "docs", withIntermediateDirectories: true)
for (n, name) in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (32, "favicon-32.png")] {
    render(n, "docs/" + name)
}

/// The share image (1200 x 630): state navy, the pie slice on a plum tile at the left, the name and tagline at the right, and a row
/// of firs along the bottom.
func og(_ path: String) {
    let W = 1200, H = 630
    let ctx = canvas(W, H)
    ctx.setFillColor(rgb(NAVY)); ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
    ctx.setFillColor(rgb(PLUM))
    ctx.addPath(CGPath(roundedRect: CGRect(x: 60, y: 120, width: 440, height: 440), cornerWidth: 96, cornerHeight: 96, transform: nil)); ctx.fillPath()
    ctx.saveGState(); ctx.translateBy(x: 60, y: 120); pie(ctx, 440); ctx.restoreGState()
    // firs along the bottom
    ctx.setFillColor(rgb(FIR))
    var x: CGFloat = 8
    while x < CGFloat(W) { ctx.move(to: CGPoint(x: x, y: 0)); ctx.addLine(to: CGPoint(x: x + 16, y: 42)); ctx.addLine(to: CGPoint(x: x + 32, y: 0)); ctx.fillPath(); x += 44 }
    let ns = NSGraphicsContext(cgContext: ctx, flipped: false)
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = ns
    let title = NSFont(name: "AvenirNextCondensed-Heavy", size: 104) ?? NSFont.boldSystemFont(ofSize: 96)
    let sub = NSFont(name: "AvenirNextCondensed-DemiBold", size: 44) ?? NSFont.boldSystemFont(ofSize: 40)
    NSAttributedString(string: "OREGON EATS", attributes: [.font: title, .foregroundColor: NSColor.white]).draw(at: NSPoint(x: 548, y: 330))
    NSAttributedString(string: "FOOD CARTS, BREWPUBS & CHOWDER", attributes: [.font: sub, .foregroundColor: NSColor(cgColor: rgb(GOLD))!]).draw(at: NSPoint(x: 552, y: 270))
    NSGraphicsContext.restoreGraphicsState()
    save(ctx, path)
}
og("docs/og.png")
