// Oregon Eats icon concepts for Nick's pick, in the shared Eats Ranked icon style (state-prompts/ICON-STYLE.md v1):
// one flat, level, centred food on a plain background; no scenery, tilt, texture, gloss or gradients.
// Usage (from or-eats/): swift scripts/icon-concepts.swift   -> playbook/brand/concept-{a,b,c}-1024.png and -512, -180, -60 copies
//   A  Dungeness crab (the state crustacean): plan view, cooked orange with cream claw tips, on state navy
//   B  marionberry pie (the state pie, HCR 19 of 2017): a slice in front view with a lighter top crust, on marionberry plum
//   C  hazelnuts (the state nut): two nuts side by side with their pale bases, on state navy
// Palette candidates (the prompt's; Nick's call): state navy #14305C and gold #F2B705 (ORS 186.010), or the landscape set: Douglas
// fir #2E5E4E, Crater Lake blue #1F5A96, marionberry #5A1F46, cream #F7F3EA. Food-only tones are listed per concept.
import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func rgb(_ hex: UInt32) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 255) / 255, green: CGFloat((hex >> 8) & 255) / 255, blue: CGFloat(hex & 255) / 255, alpha: 1)
}
let NAVY: UInt32 = 0x14305C, PLUM: UInt32 = 0x5A1F46, CREAM: UInt32 = 0xF7F3EA

// MARK: A, Dungeness crab (recognised from above: plan view). CoreGraphics y-up. Legs and claws in the base orange, the carapace a
// lighter top plane, cream pincer tips. Box about 0.72 x 0.62, mass a little low.
func crab(_ c: CGContext, _ s: CGFloat) {
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    func E(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect { CGRect(x: (x - w / 2) * s, y: (y - h / 2) * s, width: w * s, height: h * s) }
    let base = rgb(0xE8642E), top = rgb(0xF3925C), tip = rgb(0xF7E4C8)
    c.setLineCap(.round); c.setLineJoin(.round)
    // walking legs: 4 a side, each a two-segment 46 px stroke out from the shell and down
    c.setStrokeColor(base); c.setLineWidth(0.045 * s)
    for side in [-1.0, 1.0] as [CGFloat] {
        for k in 0..<4 {
            let kk = CGFloat(k)
            let leg = CGMutablePath()
            leg.move(to: P(0.5 + side * 0.16, 0.49 - 0.05 * kk))
            leg.addLine(to: P(0.5 + side * 0.285, 0.535 - 0.07 * kk))
            leg.addLine(to: P(0.5 + side * 0.345, 0.45 - 0.085 * kk))
            c.addPath(leg); c.strokePath()
        }
    }
    // claws: an arm from the shell's front corner up and out, then the pincer (an upright ellipse), its tip cream, split by a notch
    for side in [-1.0, 1.0] as [CGFloat] {
        let arm = CGMutablePath()
        arm.move(to: P(0.5 + side * 0.12, 0.56)); arm.addLine(to: P(0.5 + side * 0.215, 0.665))
        c.setStrokeColor(base); c.setLineWidth(0.062 * s); c.addPath(arm); c.strokePath()
        let cx = 0.5 + side * 0.235
        let claw = CGPath(ellipseIn: E(cx, 0.745, 0.13, 0.17), transform: nil)
        c.saveGState(); c.addPath(claw); c.clip()
        c.setFillColor(base); c.fill(CGRect(x: 0, y: 0, width: s, height: s))
        c.setFillColor(tip); c.fill(CGRect(x: 0, y: 0.78 * s, width: s, height: s))          // cream pincer tips
        c.restoreGState()
        // the gap between the pincers: a wedge cut to the background from the top
        let notch = CGMutablePath()
        notch.move(to: P(cx - side * 0.012, 0.84)); notch.addLine(to: P(cx + side * 0.004, 0.755)); notch.addLine(to: P(cx + side * 0.04, 0.84))
        notch.closeSubpath()
        c.setFillColor(rgb(NAVY)); c.addPath(notch); c.fillPath()
    }
    // carapace: wider than long, the lighter top plane, over the leg roots
    c.setFillColor(top); c.fillEllipse(in: E(0.5, 0.465, 0.42, 0.30))
    // eyes: two dark dots on the front edge (2 marks, 40 px)
    c.setFillColor(rgb(NAVY))
    c.fillEllipse(in: E(0.46, 0.585, 0.04, 0.04)); c.fillEllipse(in: E(0.54, 0.585, 0.04, 0.04))
}

// MARK: B, marionberry pie slice (front view of the cut face, one lighter top plane). The point of the slice at the left, the fluted
// rim at the right. Crust in three tones of one material, the filling in two berry tones.
func pie(_ c: CGContext, _ s: CGFloat) {
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    func R(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect { CGRect(x: x * s, y: y * s, width: w * s, height: h * s) }
    let crust = rgb(0xC98A3E), crustTop = rgb(0xE0A95E), crustLow = rgb(0xA8622A), berry = rgb(0x7A2E62)
    // top crust plane: from the point (left) widening to the rim (right)
    let topPlane = CGMutablePath()
    topPlane.move(to: P(0.14, 0.52)); topPlane.addLine(to: P(0.80, 0.52)); topPlane.addLine(to: P(0.80, 0.67)); topPlane.closeSubpath()
    c.setFillColor(crustTop); c.addPath(topPlane); c.fillPath()
    // the cut face: bottom crust, berry filling, a thin top crust
    c.setFillColor(crustLow); c.fill(R(0.14, 0.31, 0.66, 0.055))
    c.setFillColor(berry); c.fill(R(0.14, 0.365, 0.66, 0.125))
    c.setFillColor(crust); c.fill(R(0.14, 0.49, 0.66, 0.03))
    // the fluted rim at the wide end: a tall rounded crust block
    c.setFillColor(crust); c.addPath(CGPath(roundedRect: R(0.765, 0.31, 0.095, 0.385), cornerWidth: 0.045 * s, cornerHeight: 0.045 * s, transform: nil)); c.fillPath()
    // vents in the top crust: 3 berry slits (34 px round-cap strokes)
    c.setStrokeColor(berry); c.setLineWidth(0.034 * s); c.setLineCap(.round)
    for (x0, x1, y) in [(0.42, 0.50, 0.555), (0.56, 0.66, 0.565), (0.60, 0.70, 0.615)] as [(CGFloat, CGFloat, CGFloat)] {
        c.move(to: P(x0, y)); c.addLine(to: P(x1, y)); c.strokePath()
    }
}

// MARK: C, hazelnuts (round, front view): two nuts side by side, the right one a little lower, each with its pale flat base.
func hazelnuts(_ c: CGContext, _ s: CGFloat) {
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    let shell = rgb(0xC2803F), shellDark = rgb(0x9C5F2A), basePale = rgb(0xEAD8B0)
    func nut(_ cx: CGFloat, _ by: CGFloat, _ w: CGFloat) {
        // body: a round bottom rising to a soft point, w wide and 1.08 w tall
        let h = w * 1.08
        let body = CGMutablePath()
        body.move(to: P(cx, by + h))
        body.addCurve(to: P(cx + w / 2, by + h * 0.38), control1: P(cx + w * 0.16, by + h * 0.98), control2: P(cx + w / 2, by + h * 0.72))
        body.addCurve(to: P(cx, by), control1: P(cx + w / 2, by + h * 0.12), control2: P(cx + w * 0.28, by))
        body.addCurve(to: P(cx - w / 2, by + h * 0.38), control1: P(cx - w * 0.28, by), control2: P(cx - w / 2, by + h * 0.12))
        body.addCurve(to: P(cx, by + h), control1: P(cx - w / 2, by + h * 0.72), control2: P(cx - w * 0.16, by + h * 0.98))
        body.closeSubpath()
        c.saveGState(); c.addPath(body); c.clip()
        c.setFillColor(shell); c.fill(CGRect(x: 0, y: 0, width: s, height: s))
        c.setFillColor(shellDark); c.fill(CGRect(x: 0, y: 0, width: s, height: (by + h * 0.30) * s))    // darker underside
        c.setFillColor(basePale); c.fillEllipse(in: CGRect(x: (cx - w * 0.30) * s, y: (by - h * 0.06) * s, width: w * 0.60 * s, height: h * 0.24 * s))
        c.restoreGState()
    }
    // the left nut sits behind: draw it first, then a navy gap ring and the right nut
    nut(0.335, 0.32, 0.37)
    let w: CGFloat = 0.38, cx: CGFloat = 0.665, by: CGFloat = 0.275, h = w * 1.08
    let ring = CGMutablePath()
    ring.addEllipse(in: CGRect(x: (cx - w / 2) * s, y: by * s, width: w * s, height: h * 0.80 * s))
    c.setStrokeColor(rgb(NAVY)); c.setLineWidth(0.026 * s); c.addPath(ring); c.strokePath()
    nut(cx, by, w)
}

// MARK: - main
let root = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent().deletingLastPathComponent().path
let out = root + "/playbook/brand"
try? FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
func canvas(_ n: Int) -> CGContext {
    let c = CGContext(data: nil, width: n, height: n, bitsPerComponent: 8, bytesPerRow: 0,
                      space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    c.setAllowsAntialiasing(true); c.setShouldAntialias(true); c.interpolationQuality = .high
    return c
}
func save(_ img: CGImage, _ name: String) {
    let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: out + "/" + name) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, img, nil)
    guard CGImageDestinationFinalize(dest) else { fatalError("could not write \(name)") }
}
for (key, bg, draw) in [("a", NAVY, crab), ("b", PLUM, pie), ("c", NAVY, hazelnuts)] as [(String, UInt32, (CGContext, CGFloat) -> Void)] {
    let c = canvas(1024)
    c.setFillColor(rgb(bg)); c.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
    draw(c, 1024)
    let full = c.makeImage()!
    save(full, "concept-\(key)-1024.png")
    for n in [512, 180, 60] {
        let sm = canvas(n); sm.draw(full, in: CGRect(x: 0, y: 0, width: n, height: n)); save(sm.makeImage()!, "concept-\(key)-\(n).png")
    }
    print("wrote concept-\(key)")
}
