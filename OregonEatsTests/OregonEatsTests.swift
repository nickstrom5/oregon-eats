import XCTest
import CoreLocation
@testable import OregonEats

@MainActor
final class OregonEatsTests: XCTestCase {

    /// A tiny core file and two region detail files with the same shape as Resources/places.json and Resources/detail-*.json.
    private func sampleModel() async throws -> AppModel {
        let json = """
        {"v":1,"generated":"2026-10-24","overture_release":"2026-10-21.0","liquor_updated":"2026-10-24","licenses_updated":"2026-10-24",
         "olcc_active_onprem":8772,"olcc_active_full":5173,"inspections_through":{},
         "cities":["Portland","Newport","Bend","McMinnville","Lincoln City","Sandy"],
         "cuisines":["Bar & Pub","Seafood","Bakery & Sweets","Italian","American & Other","Mexican"],
         "brands":["Burgerville"],"counties":["Multnomah County","Lincoln County","Deschutes County","Yamhill County","Clackamas County"],
         "regions":["Portland Metro","Willamette Valley","Oregon Coast","Southern Oregon","Central Oregon","Gorge & Eastern Oregon"],
         "srcs":["official","meta","AllThePlaces","DAC","research"],"results":[],
         "count":8,"count_restaurants":7,
         "calibration":{"Oregon (statewide)":{"listings":23811,"groups":{"meta_high":{"n":8981,"official":0.466}}},"Multnomah County (Portland)":{"groups":{"meta_high":{"n":2483,"official":0.528}}}},
         "places":[
          {"id":"a","n":"Dan & Louis Oyster Bar","c":0,"co":0,"rg":0,"cu":1,"t":2,"s":1,"hc":1,"g":128,"f":1907,"a":"208 SW Ankeny St","z":"97204","la":45.5225,"lo":-122.6726,"liq":1,"dish":"oyster stew"},
          {"id":"b","n":"Mo's Seafood & Chowder","c":1,"co":1,"rg":2,"cu":1,"t":2,"s":1,"hc":1,"g":4,"a":"622 SW Bay Blvd","la":44.627,"lo":-124.057,"liq":1},
          {"id":"c","n":"Bark City BBQ","c":0,"co":0,"rg":0,"cu":4,"t":0,"s":1,"hc":1,"g":1,"a":"4727 SE Woodstock Blvd","la":45.479,"lo":-122.615},
          {"id":"d","n":"Deschutes Brewery","c":2,"co":2,"rg":4,"cu":0,"t":2,"s":1,"g":2,"liq":1,"a":"1044 NW Bond St","la":44.059,"lo":-121.314},
          {"id":"e","n":"Dotty's","c":0,"co":0,"rg":0,"cu":4,"t":2,"s":0,"v":1,"la":45.50,"lo":-122.60},
          {"id":"f","n":"Nick's Italian Cafe","c":3,"co":3,"rg":1,"cu":3,"t":2,"s":1,"hc":1,"g":16,"h":1,"jbf":"America's Classics 2014","ip":60,"a":"521 NE 3rd St","la":45.21,"lo":-123.19,"liq":1},
          {"id":"g","n":"Otis Cafe","c":4,"co":1,"rg":2,"cu":4,"t":1,"s":1,"hc":1,"g":8,"a":"4618 SE Highway 101","la":44.93,"lo":-124.02},
          {"id":"h","n":"Joe's Donut Shop","c":5,"co":4,"rg":0,"cu":2,"t":1,"s":1,"g":32,"la":45.40,"lo":-122.26}
         ]}
        """
        let metro = """
        {"a":{"lic":[["OLCC liquor license","123456","Full On-Premises (beer, wine, spirits)","2027-03-31"]],"ph":"(503) 227-5906","w":"danandlouis.com"},
         "c":{"w":"javascript:alert(1)"}}
        """
        let coast = """
        {"b":{"lic":[["OLCC liquor license","234567","Full On-Premises (beer, wine, spirits)","2027-06-30"],["OLCC liquor license",null,"Limited On-Premises (beer, wine, cider)"]]}}
        """
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("or-test-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let url = dir.appendingPathComponent("places.json")
        try json.data(using: .utf8)!.write(to: url)
        try metro.data(using: .utf8)!.write(to: dir.appendingPathComponent("detail-portland-metro.json"))
        try coast.data(using: .utf8)!.write(to: dir.appendingPathComponent("detail-oregon-coast.json"))
        let model = AppModel(defaults: UserDefaults(suiteName: "test-\(UUID().uuidString)")!)
        await model.load(from: url, detailFolder: dir)
        XCTAssertTrue(model.isLoaded, model.loadError ?? "")
        return model
    }

    func testDecodesAndHidesNonRestaurantsByDefault() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.places.count, 8)
        XCTAssertEqual(m.restaurantCount, 7)
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Dotty's" }, "a video-lottery parlor is hidden by default")
        m.filters.includeNonRestaurants = true
        XCTAssertTrue(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Dotty's" })
    }

    func testGuidesListOnlyWhatTheyPromise() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.list(.foodCarts, sort: .name, search: "", here: nil).map(\.name), ["Bark City BBQ"])
        XCTAssertEqual(m.list(.coastSeafood, sort: .name, search: "", here: nil).map(\.name), ["Mo's Seafood & Chowder"])
        XCTAssertEqual(m.list(.marionberry, sort: .name, search: "", here: nil).map(\.name), ["Otis Cafe"])
        XCTAssertEqual(m.list(.wineCountry, sort: .name, search: "", here: nil).map(\.name), ["Nick's Italian Cafe"])
        XCTAssertEqual(m.list(.doughnuts, sort: .name, search: "", here: nil).map(\.name), [], "a doughnut tag without a hand check isn't listed")
        XCTAssertEqual(m.list(.brewpubs, sort: .name, search: "", here: nil).map(\.name), ["Deschutes Brewery"], "brewpubs come from the license, no hand check needed")
        XCTAssertEqual(m.list(.oldest, sort: .oldest, search: "", here: nil).map(\.name), ["Dan & Louis Oyster Bar"])
        XCTAssertEqual(m.list(.honors, sort: .iconic, search: "", here: nil).map(\.name), ["Nick's Italian Cafe"])
        XCTAssertEqual(m.count(.taquerias), 0)
        XCTAssertFalse(Guide.brewpubs.isHandChecked); XCTAssertTrue(Guide.foodCarts.isHandChecked)
    }

    func testDatesAreCalendarDays() {
        var utc = Calendar(identifier: .gregorian)
        utc.timeZone = TimeZone(identifier: "UTC")!
        let d = DayFormat.date("2026-06-16")!
        XCTAssertEqual(utc.dateComponents([.year, .month, .day], from: d), DateComponents(year: 2026, month: 6, day: 16))
        XCTAssertTrue(DayFormat.monthYear("2025-09-01")!.contains("2025"))
        XCTAssertNil(DayFormat.date("2026-13-01"))
        XCTAssertEqual(DayFormat.text("soon"), "soon", "a value that isn't a date is shown as it is")
    }

    func testRegionDetailsLoadOnDemand() async throws {
        let m = try await sampleModel()
        let v = await m.detail(for: m.place(id: "a")!)
        XCTAssertEqual(v?.licenses.first?.source, "OLCC liquor license")
        XCTAssertEqual(v?.licenses.first?.id, "123456")
        XCTAssertEqual(v?.licenses.first?.expires, "2027-03-31", "OLCC's expiration date comes through")
        XCTAssertEqual(v?.website?.absoluteString, "https://danandlouis.com", "a bare host gets https://")
        let cart = await m.detail(for: m.place(id: "c")!)
        XCTAssertNil(cart?.website, "a javascript: link never becomes a website button")
        let mos = await m.detail(for: m.place(id: "b")!)
        XCTAssertEqual(mos?.licenses.count, 2, "the Oregon Coast file is read on its own")
        XCTAssertNil(mos?.licenses.last?.expires, "a license row without an expiration date still decodes")
        XCTAssertEqual(AppModel.regionSlug("Gorge & Eastern Oregon"), "gorge-eastern-oregon")
        XCTAssertEqual(AppModel.regionSlug("Portland Metro"), "portland-metro")
        let missing = await m.detail(for: m.place(id: "d")!)
        XCTAssertNil(missing, "a region with no detail file reads as no detail, not a crash")
    }

    func testSearchWordStartsTownsAndGuides() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.list(.all, sort: .name, search: "ank", here: nil).map(\.name), ["Dan & Louis Oyster Bar"], "a street word start")
        XCTAssertEqual(m.list(.all, sort: .name, search: "newport", here: nil).map(\.name), ["Mo's Seafood & Chowder"], "a town narrows to it")
        XCTAssertEqual(m.list(.all, sort: .name, search: "oyster stew", here: nil).map(\.name), ["Dan & Louis Oyster Bar"], "a dish finds who serves it")
        XCTAssertEqual(m.list(.all, sort: .name, search: "🍕", here: nil), [], "an emoji finds nothing, not everything")
        XCTAssertEqual(m.list(.all, sort: .name, search: "food carts", here: nil).map(\.name), ["Bark City BBQ"], "a guide word means the guide")
        XCTAssertEqual(m.list(.all, sort: .name, search: "lincoln city", here: nil).map(\.name), ["Otis Cafe"], "a two-word town")
    }

    func testOutsideOregonUsesTheOutline() {
        func inside(_ la: Double, _ lo: Double) -> Bool { OregonOutline.contains(CLLocationCoordinate2D(latitude: la, longitude: lo)) }
        XCTAssertTrue(inside(45.52, -122.68), "Portland"); XCTAssertTrue(inside(46.19, -123.83), "Astoria"); XCTAssertTrue(inside(42.05, -124.28), "Brookings")
        XCTAssertTrue(inside(44.03, -116.96), "Ontario"); XCTAssertTrue(inside(45.93, -118.39), "Milton-Freewater"); XCTAssertTrue(inside(42.22, -121.78), "Klamath Falls")
        XCTAssertFalse(inside(43.62, -116.20), "Boise"); XCTAssertFalse(inside(46.06, -118.34), "Walla Walla")
        XCTAssertFalse(inside(41.76, -124.20), "Crescent City"); XCTAssertFalse(inside(47.61, -122.33), "Seattle")
        XCTAssertFalse(inside(37.33, -122.03), "Cupertino")
    }

    func testMatchRatesComeFromTheLicenseList() async throws {
        let m = try await sampleModel()
        XCTAssertNil(m.matchRate(for: m.place(id: "a")!), "an official record needs no listing rate")
        XCTAssertEqual(m.matchRate(for: m.place(id: "g")!), "47–53%")
    }

    func testBundledData() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "bundle-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        XCTAssertGreaterThan(m.restaurantCount, 11_000)
        XCTAssertGreaterThan(m.licensedCount, 5_000, "thousands of restaurants hold an OLCC license")
        XCTAssertGreaterThan(m.count(.brewpubs), 200, "OLCC's Brewery Public House licenses")
        XCTAssertGreaterThan(m.count(.foodCarts), 20)
        XCTAssertEqual(Set(m.places.map(\.id)).count, m.places.count, "ids are unique")
        for g in Guide.allCases where g.isHandChecked {
            XCTAssertTrue(m.places.filter(g.includes).allSatisfy(\.handChecked), "\(g.title) lists only hand-checked places")
        }
        XCTAssertTrue(m.places.allSatisfy { $0.michelin == .none }, "Oregon has no MICHELIN Guide")
        // no Google-derived data: the data file has no rating, review or price fields at all
        let raw = try String(contentsOf: Bundle.main.url(forResource: "places", withExtension: "json")!, encoding: .utf8)
        for key in ["\"rating\"", "\"reviews\"", "\"price\"", "\"gmap_id\""] { XCTAssertFalse(raw.contains(key), "\(key) must not ship") }
        // hand-checked facts the research settled (playbook: name a known place so a merge can't silently lose it)
        let dl = try XCTUnwrap(m.places.first { $0.name == "Dan & Louis Oyster Bar" && $0.city == "Portland" })
        XCTAssertEqual(dl.founded, 1907); XCTAssertTrue(dl.handChecked)
        let gt = try XCTUnwrap(m.places.first { $0.name == "Golden Triangle Asian Fusion" })
        XCTAssertTrue(gt.address?.hasPrefix("4727 ") ?? false, "the cart sits at its Woodstock pod, not its old listing 2.5 km away")
        XCTAssertFalse(m.places.contains { $0.name == "Big Ski's Pierogis" }, "closed Sept. 2026 (Bend Bulletin)")
        XCTAssertNil(m.places.first { $0.name == "Otis Cafe" && $0.city == "Otis" }, "the café moved to Lincoln City")
    }

    /// Stable ids: md5(name + ~100 m cell)[:12], never a row number; every bundled region detail file decodes and its ids are core ids.
    func testIdsAndBundledDetailFiles() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "ids-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.places.allSatisfy { $0.id.count >= 12 && $0.id.prefix(12).allSatisfy(\.isHexDigit) && $0.id.dropFirst(12).allSatisfy { $0 == "x" } })
        let ids = Set(m.places.map(\.id))
        var licensed = 0
        for region in Set(m.places.compactMap(\.region)) {
            let url = try XCTUnwrap(Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json"), region)
            let d = try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url))
            XCTAssertTrue(Set(d.keys).isSubset(of: ids), "\(region) detail ids are core ids")
            licensed += d.values.filter { $0.licenses.contains { $0.source == "OLCC liquor license" } }.count
            XCTAssertTrue(d.values.allSatisfy { $0.licenses.allSatisfy { l in l.expires.map { DayFormat.date($0) != nil } ?? true } }, "expiration dates are dates")
        }
        XCTAssertGreaterThan(licensed, 5_000, "licensed places carry their OLCC license")
    }

    func testBundledDataGuards() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "guards-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        XCTAssertEqual(DataGuards.adultVenues(m.places), [], "no strip club under its name")
        XCTAssertEqual(DataGuards.adultAddresses(m.places), [], "no place at a checked adult-club address")
        XCTAssertEqual(DataGuards.gamingParlors(m.places), [], "no video-lottery parlor among the restaurants")
        XCTAssertEqual(DataGuards.badWebsites(try DataGuards.bundledLinks(m.places)), [], "no directory, Google or news page as a restaurant's website")
        XCTAssertEqual(DataGuards.badNames(m.places), [], "no visible name ending in \u{201C} the\u{201D} or \u{201C} of\u{201D}, or just \u{201C}The\u{201D}")
        XCTAssertEqual(DataGuards.legalNames(m.places), [], "no license holder entity name (\u{201C}… LLC\u{201D}) shown as a place's name")
        XCTAssertEqual(DataGuards.nonRestaurants(m.places), [], "no nail salon, senior home, gun store or gas station among the restaurants")
    }

    /// Each guard above fires on a copy of the bundled data broken the way QA found it elsewhere: a guard that can't fail guards nothing.
    func testGuardsCatchABrokenCopy() async throws {
        let raw = try Data(contentsOf: Bundle.main.url(forResource: "places", withExtension: "json")!)
        var file = try XCTUnwrap(JSONSerialization.jsonObject(with: raw) as? [String: Any])
        var places = try XCTUnwrap(file["places"] as? [[String: Any]])
        let idx = places.indices.filter { places[$0]["v"] == nil }.prefix(9).map { $0 }
        places[idx[2]]["n"] = "Stars Cabaret"
        places[idx[3]]["n"] = "Kitchen the"
        places[idx[4]]["n"] = "PACIFIC HOSPITALITY GROUP LLC"
        places[idx[5]]["n"] = "Tipsy Nails & Spa"
        places[idx[6]]["n"] = "Dotty's"
        places[idx[7]]["a"] = "8325 SE McLoughlin Blvd"; places[idx[7]]["c"] = (file["cities"] as? [String])?.firstIndex(of: "Portland")
        places[idx[8]]["n"] = "The Meltdown"
        file["places"] = places
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("places-broken.json")
        try JSONSerialization.data(withJSONObject: file).write(to: url)
        let m = AppModel(defaults: UserDefaults(suiteName: "broken-\(UUID().uuidString)")!)
        await m.load(from: url)
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        let id = idx.map { places[$0]["id"] as? String }
        func caught(_ found: [String], _ i: Int, _ what: String) {
            XCTAssertTrue(found.contains { $0.contains("[\(id[i] ?? "?")]") }, "the guard missed \(what)")
        }
        let links = [(name: "A", id: "x1", url: "https://www.yelp.com/biz/some-place"), (name: "B", id: "x2", url: "https://www.oregonlive.com/dining/2026/"),
                     (name: "C", id: "x3", url: "https://smart.com/menu")]
        XCTAssertEqual(DataGuards.badWebsites(links).count, 2, "the guard catches a Yelp page and a news story, and not smart.com")
        caught(DataGuards.adultVenues(m.places), 2, "a strip club")
        caught(DataGuards.badNames(m.places), 3, "\u{201C}Kitchen the\u{201D}")
        caught(DataGuards.legalNames(m.places), 4, "a license holder's entity name")
        caught(DataGuards.nonRestaurants(m.places), 5, "a nail salon shown as a restaurant")
        caught(DataGuards.gamingParlors(m.places), 6, "a video-lottery chain shown as a restaurant")
        caught(DataGuards.adultAddresses(m.places), 7, "a place at the Acropolis Club's address")
        caught(DataGuards.nonRestaurants(m.places), 8, "a Denny's delivery-only brand shown as a restaurant (QA 2026-10-29)")
    }
}

/// Checks on the bundled data, written as functions so testGuardsCatchABrokenCopy can prove each one fires.
enum DataGuards {
    /// directories, Google and news sites: matched on the link's host, so "smart.com" isn't "rt.com"
    static let badHosts = #"^https?://([^/?#]*\.)?(yelp\.com|business\.site|google\.com|groupon\.com|yellowpages\.com|tripadvisor\.com|oregonlive\.com|wweek\.com|portlandmercury\.com|kgw\.com|koin\.com|katu\.com|opb\.org|bendbulletin\.com|registerguard\.com|statesmanjournal\.com|eater\.com|travelportland\.com|traveloregon\.com|rt\.com)([:/?#]|$)"#

    static func badWebsites(_ links: [(name: String, id: String, url: String)]) -> [String] {
        links.compactMap { l in
            guard l.url.range(of: badHosts, options: [.regularExpression, .caseInsensitive]) != nil else { return nil }
            return "\(l.name) [\(l.id)]: \(l.url)"
        }
    }

    /// every website link in the bundled region detail files, with its place's name
    static func bundledLinks(_ places: [Place]) throws -> [(name: String, id: String, url: String)] {
        let names = Dictionary(places.map { ($0.id, $0.name) }, uniquingKeysWith: { a, _ in a })
        var out: [(name: String, id: String, url: String)] = []
        for region in Set(places.compactMap(\.region)) {
            guard let url = Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json") else { continue }
            for (id, d) in try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url)) {
                if let w = d.website?.absoluteString { out.append((names[id] ?? "?", id, w)) }
            }
        }
        return out
    }

    static let adultNames = #"gentlem[ae]n['’]?s club|strip club|exotic dancer|\bmen['’]?s club|rick['’]?s cabaret|xtc cabaret|baby dolls|spearmint rhino|bikini bar|pt['’]?s showclub|showgirls|centerfolds|treasures? gentlem|deja ?vu showgirls|hustler club|penthouse club|stars cabaret|lucky devil lounge|devils point|casa diablo|golden dragon exotic|union jacks? club|kit kat club|bikini barista"#

    /// data/research/adult_venues.json's checked club addresses (number and street start), by town
    static let adultAddresses: [(String, String)] = [("8325 SE McLoughlin", "Portland"), ("610 NW Couch", "Portland"), ("611 NW Couch", "Portland"),
                                                     ("15 SW 2nd Ave", "Portland")]

    static func adultAddresses(_ places: [Place]) -> [String] {
        places.filter { p in adultAddresses.contains { (a, t) in p.city == t && (p.address ?? "").lowercased().hasPrefix(a.lowercased()) } }
            .map { "\($0.name) [\($0.id)]" }
    }

    /// Oregon's sourced video-poker deli chains and names that advertise gambling: listed only with the non-restaurants
    static let gamingNames = #"^(dotty['’]?s|dede['’]?s)\b|\b(lottery|lotto|jackpot|slots?|poker|gaming)\b"#

    static func gamingParlors(_ places: [Place]) -> [String] {
        places.filter { !$0.isVenue && $0.name.range(of: gamingNames, options: [.regularExpression, .caseInsensitive]) != nil }
            .map { "\($0.name) [\($0.id)]" }
    }

    /// every license key in the bundled region detail files, by place id
    static func bundledLicenses(_ places: [Place]) throws -> [String: [String]] {
        var out: [String: [String]] = [:]
        for region in Set(places.compactMap(\.region)) {
            guard let url = Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json") else { continue }
            for (id, d) in try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url)) where !d.licenses.isEmpty {
                out[id] = d.licenses.compactMap(\.id)
            }
        }
        return out
    }

    static func adultVenues(_ places: [Place]) -> [String] {
        places.filter { $0.name.range(of: adultNames, options: [.regularExpression, .caseInsensitive]) != nil }.map { "\($0.name) [\($0.id)]" }
    }

    /// a name cut off after "the" or "of" ("Kitchen the", "Wines of") or nothing but "The", among the places shown by default
    static func badNames(_ places: [Place]) -> [String] {
        places.filter { p in
            let n = p.name.trimmingCharacters(in: .whitespaces).lowercased()
            return !p.isVenue && (n.hasSuffix(" the") || n.hasSuffix(" of") || n == "the")
        }.map { "\($0.name) [\($0.id)]" }
    }

    /// OLCC's licensee_name is never shown; a business name that's still a legal entity shouldn't be either
    static let legalSuffix = #"\b(llc|l\.l\.c|inc|corp|corporation)\.?$"#

    static func legalNames(_ places: [Place]) -> [String] {
        places.filter { !$0.isVenue && $0.name.range(of: legalSuffix, options: [.regularExpression, .caseInsensitive]) != nil }
            .map { "\($0.name) [\($0.id)]" }
    }

    /// businesses that aren't places to eat, among the places shown by default
    /// and delivery-only brands cooked in another restaurant's kitchen: Denny's The Meltdown, The Burger Den and Banda Burrito (QA 2026-10-29)
    static let nonRestaurantNames = #"\bnails?\b|assisted living|gun (?:club|range|shop|store)|shooting range|firearms|petroleum|\bauto (?:repair|parts)\b|^(?:the )?(?:meltdown|burger den)$|banda burrito|tenderfix|pardon my cheesesteak|neighborhood wings"#

    static func nonRestaurants(_ places: [Place]) -> [String] {
        places.filter { !$0.isVenue && $0.name.range(of: nonRestaurantNames, options: [.regularExpression, .caseInsensitive]) != nil }
            .map { "\($0.name) [\($0.id)]" }
    }
}

/// pipeline/website_blocklist.json (hacked, taken-over, expired or another business's sites, confirmed by hand in the link sweeps):
/// no link on it may ship in any field of any JSON file the app bundles. The 2026-10-19 QA found the export had only filtered the
/// website field, or nothing, so hijacked links were still in the bundle. Read from the repo, so a new entry needs no code change.
final class LinkBlocklistTests: XCTestCase {
    func testNoBlocklistedLinkInBundledData() throws {
        let entries = try LinkBlocklist.entries()
        XCTAssertFalse(entries.isEmpty, "the blocklist is missing or empty")
        let files = LinkBlocklist.bundledJSON()
        XCTAssertFalse(files.isEmpty, "no bundled JSON found")
        var hits: [String] = []
        for url in files {
            let text = try String(contentsOf: url, encoding: .utf8)
            hits += LinkBlocklist.hits(in: text, entries).map { "\(url.lastPathComponent): \($0)" }
        }
        XCTAssertEqual(hits, [], "blocklisted links in the app's bundled data")
    }

    /// The guard fires on a copy of the bundled data broken three ways: a blocklisted domain, its subdomain, and a "url" entry.
    func testBlocklistGuardCatchesABrokenCopy() throws {
        let entries = try LinkBlocklist.entries()
        let file = try XCTUnwrap(LinkBlocklist.bundledJSON().max { (try? $0.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) ?? 0 < (try? $1.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) ?? 0 })
        let text = try String(contentsOf: file, encoding: .utf8)
        let domain = try XCTUnwrap(entries.first { ($0["match"] as? String ?? "domain") == "domain" }?["domain"] as? String)
        let fake: [[String: Any]] = entries + [["match": "url", "url": "https://example.org/hacked-page"]]
        let before = LinkBlocklist.hits(in: text, fake).count
        let broken = text + "{\"w\":\"https://www.\(domain)/menu\"}{\"src\":\"http://shop.\(domain)/\"}{\"w\":\"https://example.org/hacked-page/\"}"
        XCTAssertEqual(LinkBlocklist.hits(in: broken, fake).count, before + 3, "a domain, a subdomain and a url entry are all caught")
        XCTAssertEqual(LinkBlocklist.hits(in: "{\"w\":\"https://not\(domain)/\"}", entries), [], "a host that only ends with the domain's letters isn't it")
    }
}

enum LinkBlocklist {
    static func entries() throws -> [[String: Any]] {
        let url = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("pipeline/website_blocklist.json")
        return try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [[String: Any]])
    }

    /// every .json file in the app bundle, subfolders included
    static func bundledJSON() -> [URL] {
        let root = Bundle.main.bundleURL
        let all = FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { $0.pathExtension == "json" && !$0.path.contains("/PlugIns/") }
    }

    private static func host(_ u: URLComponents) -> String {
        var h = (u.host ?? "").lowercased()
        if h.hasSuffix(".") { h.removeLast() }
        return h.hasPrefix("www.") ? String(h.dropFirst(4)) : h
    }

    private static func trimmedPath(_ p: String) -> String { p.hasSuffix("/") ? String(p.dropLast()) : p }

    /// the links in a JSON text that an entry covers: a "domain" entry its domain and subdomains, a "url" entry that page only
    static func hits(in text: String, _ entries: [[String: Any]]) -> [String] {
        let t = text.replacingOccurrences(of: "\\/", with: "/")
        let rx = try! NSRegularExpression(pattern: #"https?://[^"\s\\]+"#, options: [.caseInsensitive])
        return rx.matches(in: t, range: NSRange(t.startIndex..., in: t)).compactMap { m -> String? in
            let s = String(t[Range(m.range, in: t)!])
            guard let u = URLComponents(string: s) else { return nil }
            let h = host(u)
            for e in entries {
                if (e["match"] as? String ?? "domain") == "url" {
                    guard let v = URLComponents(string: e["url"] as? String ?? "") else { continue }
                    if !h.isEmpty && h == host(v) && trimmedPath(u.path) == trimmedPath(v.path) { return s }
                } else {
                    var d = (e["domain"] as? String ?? "").lowercased()
                    if let r = d.range(of: "://") { d = String(d[r.upperBound...]) }
                    d = String(d.split(separator: "/").first ?? "")
                    if d.hasPrefix("www.") { d = String(d.dropFirst(4)) }
                    if !d.isEmpty && (h == d || h.hasSuffix("." + d)) { return s }
                }
            }
            return nil
        }
    }
}

/// QA 2026-10-19, P1 3a: the support address is nick@eatsranked.com (Nick, 2026-10-12). The old Gmail address must not come back
/// anywhere in the app's source or bundled files.
final class SupportEmailTests: XCTestCase {
    func testSupportEmailIsEatsRanked() {
        XCTAssertEqual(Links.supportEmail, "nick@eatsranked.com")
    }

    func testNoGmailInAppSource() throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("OregonEats")
        XCTAssertGreaterThan(SupportEmailScan.textFiles(under: root).count, 5, "the app's source folder wasn't found")
        XCTAssertEqual(SupportEmailScan.hits(under: root), [], "the app's source still has a Gmail address")
    }

    /// The guard fires on a broken copy: a folder with one planted Gmail address.
    func testGmailGuardCatchesABrokenCopy() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir.appendingPathComponent("App"), withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        try "static let supportEmail = \"someone@GMAIL.com\"\n".write(to: dir.appendingPathComponent("App/Links.swift"), atomically: true, encoding: .utf8)
        try "{\"ok\": \"nick@eatsranked.com\"}".write(to: dir.appendingPathComponent("App/data.json"), atomically: true, encoding: .utf8)
        XCTAssertEqual(SupportEmailScan.hits(under: dir), ["App/Links.swift"])
    }
}

enum SupportEmailScan {
    static let textExtensions: Set<String> = ["swift", "plist", "json", "strings", "xcstrings", "xcprivacy", "md", "txt", "html", "entitlements"]

    static func textFiles(under root: URL) -> [URL] {
        let all = FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { textExtensions.contains($0.pathExtension.lowercased()) }
    }

    /// paths (relative to root) of text files that mention gmail.com, in any case
    static func hits(under root: URL) -> [String] {
        let base = root.resolvingSymlinksInPath().path + "/"
        return textFiles(under: root).compactMap { url in
            guard let text = try? String(contentsOf: url, encoding: .utf8),
                  text.range(of: "gmail.com", options: .caseInsensitive) != nil else { return nil }
            return url.resolvingSymlinksInPath().path.replacingOccurrences(of: base, with: "")
        }.sorted()
    }
}

/// QA 2026-10-19, P1 #13: outbound links ship without tracking tags (ref=google, referrer=google_food_ordering, cn_channel, utm_* …).
/// pipeline/tracking_params.py strips them in the export; these are the same rules.
final class TrackingParamTests: XCTestCase {
    func testNoTrackingParametersInBundledLinks() throws {
        let files = TrackingParams.bundledJSON()
        XCTAssertFalse(files.isEmpty, "no bundled JSON found")
        var hits: [String] = []
        for url in files {
            let text = try String(contentsOf: url, encoding: .utf8)
            hits += TrackingParams.tracked(in: text).map { "\(url.lastPathComponent): \($0)" }
        }
        XCTAssertEqual(hits, [], "links with tracking parameters in the app's bundled data")
    }

    /// The guard fires on a broken copy (four kinds of tracking tag, one in escaped JSON) and leaves a store's own parameters alone.
    func testTrackingGuardCatchesABrokenCopy() {
        let broken = #"[{"w":"https:\/\/places.example.com\/menu?ref=google"},{"w":"https://a.example/?utm_source=gmb&store=4"},"#
            + #"{"w":"https://b.example/x?referrer=google_food_ordering"},{"w":"https://c.example/order/1?cn_channel=cn_google"}]"#
        XCTAssertEqual(TrackingParams.tracked(in: broken).count, 4)
        let clean = #"[{"w":"https://order.example.com/menu?restaurantId=51&location=7"},{"w":"https://shop.example.com/?cid=12&ref=gs"}]"#
        XCTAssertEqual(TrackingParams.tracked(in: clean), [])
    }
}

enum TrackingParams {
    /// tracking by name, whatever the value
    static let keys = try! NSRegularExpression(pattern: #"^(?:utm[_-].*|gclid|gbraid|wbraid|dclid|fbclid|msclkid|mc_cid|mc_eid|_ga|_gl|igsh|"#
        + #"igshid|mibextid|srsltid|cn_channel|y_source|rwg_token|olonwp|ost_redirect_attribution|cmpid|yext_?.*)$"#, options: [.caseInsensitive])
    /// tracking only with these values
    static let values: [String: String] = ["ref": #"^(?:google|gmb|gbp|yext|bookmarks)\b"#, "referrer": "^google",
                                           "source": #"^(?:google|gmb|gbp|yext)\b"#, "cid": "^RF:YXT", "cmp": "^OKC-"]

    /// every .json file in the app bundle, subfolders included
    static func bundledJSON() -> [URL] {
        let all = FileManager.default.enumerator(at: Bundle.main.bundleURL, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { $0.pathExtension == "json" && !$0.path.contains("/PlugIns/") }
    }

    static func isTracking(_ key: String, _ value: String) -> Bool {
        let k = key.trimmingCharacters(in: .whitespaces)
        if keys.firstMatch(in: k, range: NSRange(k.startIndex..., in: k)) != nil { return true }
        guard let pattern = values[k.lowercased()] else { return false }
        return value.trimmingCharacters(in: .whitespaces).range(of: pattern, options: [.regularExpression, .caseInsensitive]) != nil
    }

    /// links in a JSON text whose query carries a tracking parameter
    static func tracked(in text: String) -> [String] {
        let t = text.replacingOccurrences(of: "\\/", with: "/")
        let rx = try! NSRegularExpression(pattern: #"https?://[^\s"'<>\\]+"#)
        return rx.matches(in: t, range: NSRange(t.startIndex..., in: t)).compactMap { m -> String? in
            let s = String(t[Range(m.range, in: t)!])
            guard let q = s.split(separator: "?", maxSplits: 1).dropFirst().first else { return nil }
            let query = q.split(separator: "#", maxSplits: 1, omittingEmptySubsequences: false).first ?? ""
            for part in query.split(separator: "&") {
                let kv = part.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
                let k = String(kv[0]).replacingOccurrences(of: "+", with: " ").removingPercentEncoding ?? String(kv[0])
                let v = kv.count > 1 ? (String(kv[1]).replacingOccurrences(of: "+", with: " ").removingPercentEncoding ?? String(kv[1])) : ""
                if isTracking(k, v) { return s }
            }
            return nil
        }
    }
}
