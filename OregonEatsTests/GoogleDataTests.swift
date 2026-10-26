import XCTest
@testable import OregonEats

/// The app ships no Google-derived field or figure (STATE_EATS_PLAYBOOK.md: Google data stays in the private web build), and its
/// bundle is published byte for byte as the over-the-air copy in docs/data/app/. QA OR-1 (2026-10-26) found calibration.<area>.groups
/// .<group>.google21_open, Google 2021's open share for each listing group, in both; pipeline/oregon.py now refuses to write it.
final class GoogleDataTests: XCTestCase {

    /// Every bundled JSON file and every file of the over-the-air copy: no key anywhere names Google or a star-rating field, and no
    /// text says google21.
    func testNoGoogleDerivedKeysInTheBundleOrTheOverTheAirCopy() throws {
        let ota = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("docs/data/app")
        let published = (try? FileManager.default.contentsOfDirectory(at: ota, includingPropertiesForKeys: nil)) ?? []
        XCTAssertTrue(published.contains { $0.lastPathComponent.hasPrefix("places-") }, "the over-the-air copy wasn't found in docs/data/app")
        let files = TrackingParams.bundledJSON() + published.filter { $0.pathExtension == "json" }
        XCTAssertTrue(files.contains { $0.lastPathComponent == "places.json" }, "the bundled places.json wasn't found")
        var hits: [String] = []
        for url in files {
            let data = try Data(contentsOf: url)
            hits += GoogleData.keys(in: try JSONSerialization.jsonObject(with: data)).map { "\(url.lastPathComponent): \($0)" }
            if String(decoding: data, as: UTF8.self).localizedCaseInsensitiveContains("google21") {
                hits.append("\(url.lastPathComponent): says google21")
            }
        }
        XCTAssertEqual(hits, [], "Google-derived data in the app's data")
    }

    /// The guard fires on the shape the old bundle had (a google21_open figure in a calibration group) and on a Google field on a
    /// place, and leaves the bundle's real keys alone.
    func testGoogleGuardCatchesTheOldBundlesShape() throws {
        let old = #"{"calibration":{"Oregon (statewide)":{"listings":10,"groups":{"Meta, 0.95 and up":{"n":4,"official":0.466,"full":0.3,"google21_open":0.723}}}},"#
            + #""places":[{"id":"a1","n":"Example Cafe","rating":4.5},{"id":"b2","n":"Other","price_level":2}]}"#
        let found = GoogleData.keys(in: try JSONSerialization.jsonObject(with: Data(old.utf8)))
        XCTAssertEqual(Set(found), ["calibration.Oregon (statewide).groups.Meta, 0.95 and up.google21_open", "places[0].rating", "places[1].price_level"])
        let clean = #"{"calibration":{"Oregon (statewide)":{"listings":10,"official_records":5,"groups":{"Meta, 0.95 and up":{"n":4,"official":0.466,"full":0.3}}}},"#
            + #""places":[{"id":"a1","n":"Example Cafe","liq":1,"hc":1,"jbf":"America's Classics 2014","ip":50}]}"#
        XCTAssertEqual(GoogleData.keys(in: try JSONSerialization.jsonObject(with: Data(clean.utf8))), [])
    }
}

enum GoogleData {
    /// key names the app's data may never carry: Google's (or any star-rating source's) fields, and figures from Google's 2021 data;
    /// the same rule as GOOGLE_KEY in pipeline/oregon.py
    static let key = try! NSRegularExpression(pattern: #"google|gmap|g21|rating|review|stars?$|price(?:_level|_est)?$"#, options: [.caseInsensitive])

    /// the path of every such key in a parsed JSON value
    static func keys(in value: Any, path: String = "") -> [String] {
        if let d = value as? [String: Any] {
            return d.flatMap { k, v -> [String] in
                let p = path.isEmpty ? k : "\(path).\(k)"
                let own = key.firstMatch(in: k, range: NSRange(k.startIndex..., in: k)) != nil ? [p] : []
                return own + keys(in: v, path: p)
            }
        }
        if let a = value as? [Any] {
            return a.enumerated().flatMap { i, v in keys(in: v, path: "\(path)[\(i)]") }
        }
        return []
    }
}
