import Foundation
import CoreLocation
import UIKit

/// `-screenshot <name>` opens one screen with fixed state for App Store screenshots (scripts/capture-screenshots.sh).
/// Names: home, carts, seafood, donuts, detail, map, honors, oldest, saved, about.
enum ScreenshotMode {
    /// Debug builds only: an App Store build ignores the launch argument, so no one can reach seeded screens or fake locations.
    static var name: String? {
        #if DEBUG
        let args = ProcessInfo.processInfo.arguments
        guard let i = args.firstIndex(of: "-screenshot"), i + 1 < args.count else { return nil }
        return args[i + 1]
        #else
        return nil
        #endif
    }
    static var isActive: Bool { name != nil }

    @MainActor
    static func apply(to model: AppModel) {
        guard let name, model.isLoaded else { return }
        model.filters = Filters()
        // downtown Portland (Pioneer Courthouse Square), so "nearest" lists have distances without a permission prompt
        model.screenshotLocation = CLLocation(latitude: 45.5189, longitude: -122.6793)
        // by name and town, ignoring case, so a rebuild with a slightly different casing still finds the place; the hand-checked one first.
        // Oregon publishes no inspection results, so no screenshot can show a failed one.
        let pick = { (n: String, town: String?) -> Place? in
            let hits = model.places.filter { $0.name.caseInsensitiveCompare(n) == .orderedSame && (town == nil || $0.city == town) }
            return hits.first(where: \.handChecked) ?? hits.first
        }
        for p in [pick("Dan & Louis Oyster Bar", "Portland"), pick("Mo's Seafood & Chowder", "Newport"), pick("Nick's Italian Cafe", "McMinnville")]
            .compactMap({ $0 }) where !model.isSaved(p) {
            model.toggleSaved(p)
        }
        let open = { (g: Guide) in model.tab = .guides; model.selectedGuide = g; model.guidesPath = [.guide(g)] }
        switch name {
        case "carts": open(.foodCarts)
        case "donuts": open(.doughnuts)
        case "seafood":
            // from Newport's Bayfront, so the nearest chowder and crab houses are a short drive
            model.screenshotLocation = CLLocation(latitude: 44.6270, longitude: -124.0560)
            open(.coastSeafood)
        case "honors": open(.honors)
        case "oldest": open(.oldest)
        case "detail":
            open(.honors)
            if let p = pick("Nick's Italian Cafe", "McMinnville") ?? model.places.first { model.selectedPlace = p; model.guidesPath.append(.place(p)) }
        case "map": model.tab = .map
        case "saved": model.tab = .saved
        case "about": model.tab = .about
        default: model.tab = .guides; model.selectedGuide = nil
        }
        // iPad shows the place column next to every list, so give each shot a place instead of "Pick a place": a different
        // honored or hand-checked one per shot.
        guard UIDevice.current.userInterfaceIdiom == .pad, model.selectedPlace == nil else { return }
        let place: Place? = switch name {
        case "home": pick("Dan & Louis Oyster Bar", "Portland")
        case "carts": pick("Bark City BBQ", "Portland")
        case "seafood": pick("Mo's Seafood & Chowder", "Newport")
        case "donuts": pick("Pip's Original Doughnuts and Chai", "Portland")
        case "map": pick("Dan & Louis Oyster Bar", "Portland")
        case "saved", "oldest", "honors": pick("Nick's Italian Cafe", "McMinnville")
        case "about": nil
        default: pick("Dan & Louis Oyster Bar", "Portland")
        }
        model.selectedPlace = place
    }
}
