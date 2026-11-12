"""Writes the public website in docs/ from the same data the app ships (data/app/places.json plus the data/app/detail-*.json files that
hold OLCC liquor licenses, phones and websites).

Pages: the landing page; a statewide page for each guide with at least four places (food carts and pods, brewpubs, coast seafood,
doughnut shops, wine country, taquerías; marionberry pie and the oldest places once their research has four); James Beard honors; an
explainer of Oregon's restaurant inspections (why the app shows none); one page per town with enough hand-checked or honored places to
say something real, plus a cities index; the web app (/explore/); privacy; terms; 404; sitemap.xml, robots.txt, site.webmanifest and
playbook/site-numbers.json. Everything listed is hand-checked research or public records; nothing comes from Google, Yelp or any ratings
site, and nothing is ranked by ratings. Ported from mi-eats/scripts/make-site.py.

Rules the copy keeps (scripts/qa-site.py checks them):
- Every number is counted from the data here, never typed in. OLCC's list is the state's list of liquor licenses, not of restaurants, so
  no sentence claims "every" or "all N" restaurants, and "N places with an OLCC Brewery Public House license", not "every brewpub".
- "Checked" only for the hand-checked lists (`hc`, a 2025-26 source, or an older one plus an active 2026 OLCC license, for each place).
- Oregon publishes no restaurant inspection results in bulk: the site shows none, computes no grade and says why.
- Every page carries a hash-pinned Content-Security-Policy; inline scripts and styles are hashed after the page is final.

Usage (from or-eats/): .venv/bin/python scripts/make-site.py           (github.io address, BASE /oregon-eats)
                       OR_DOMAIN=oregon.eatsranked.com .venv/bin/python scripts/make-site.py   (once Nick's CNAME resolves)
Re-run it after every data rebuild, then check the pages with scripts/qa-site.py. Never hand-edit docs/*.html.
"""
import base64
import datetime as dt
import glob
import gzip
import hashlib
import html
import json
import math
import os
import re
import struct
import urllib.parse
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = f"{ROOT}/docs"
# Where the site lives. Until Nick's Cloudflare record (CNAME oregon -> nickstrom5.github.io, DNS only) resolves, GitHub Pages serves
# the project address. When `dig oregon.eatsranked.com` shows the CNAME, run with OR_DOMAIN=oregon.eatsranked.com and push: this
# writes docs/CNAME, and GitHub then forwards the old github.io links (the ones inside shipped app builds).
CUSTOM_DOMAIN = os.environ.get("OR_DOMAIN", "").strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
REPO = "oregon-eats"
DOMAIN = f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN else f"https://nickstrom5.github.io/{REPO}"
BASE = "" if CUSTOM_DOMAIN else f"/{REPO}"     # path prefix for root-relative links
BRAND = "Oregon Eats"
APP_NAME = "Oregon Eats: Restaurants"
TAGLINE = "food carts, brewpubs & chowder"
EMAIL = "nick@eatsranked.com"   # Nick, 2026-10-12: the site's contact address (Cloudflare Email Routing)
PUBLISHED = "2026-10-24"        # the site's first publication (Article datePublished)
SITE_REV = "2026-10-24"         # the last change to this generator's own copy or code: bump it when you change the words
POLICY_UPDATED = "2026-10-24"   # privacy policy and terms: bump only when their text changes
PRIVACY_UPDATED = "2026-10-26"   # the privacy policy alone: the app's data updates (OTA-DATA.md)
CHECKED = "fall 2026"
STORAGE_PREFIX = "oreats-"      # the web app's localStorage keys (other state sites share the nickstrom5.github.io origin)
# Oregon Eats is one of the Eats Ranked state sites: the hub (eatsranked.com) lists it as a subOrganization, and every page says so
# from this side too (the footer line and the Organization's parentOrganization), in Wisconsin's words.
HUB = {"@type": "Organization", "@id": "https://eatsranked.com/#organization", "name": "Eats Ranked", "url": "https://eatsranked.com/"}
ORG_ID = f"{DOMAIN}/#org"
# the site's Organization as other pages name it (author, publisher): the same @id as the full node on the landing page
ORG_REF = {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": f"{DOMAIN}/",
           "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png", "width": 512, "height": 512}, "parentOrganization": HUB}

# ---------------------------------------------------------------- data: the core file plus the region detail files
D = json.load(open(f"{ROOT}/data/app/places.json"))
assert D.get("generated"), "data/app/places.json has no 'generated' field: the pipeline hasn't finished writing it"
DETAIL_SRC = {}
for _f in sorted(glob.glob(f"{ROOT}/data/app/detail-*.json")):
    DETAIL_SRC.update(json.load(open(_f)))
assert DETAIL_SRC, "data/app/detail-*.json are missing"


def merged(r):
    """One place with its detail fields (licenses, phone, website) put back."""
    return {**r, **(DETAIL_SRC.get(r["id"]) or {})}


RECS = [merged(r) for r in D["places"]]
TODAY = max(str(D.get("generated") or SITE_REV)[:10], SITE_REV)   # sitemap lastmod and dateModified move with the data or the copy
LIQ_UPDATED = D.get("liquor_updated") or ""
LIC_UPDATED = D.get("licenses_updated") or LIQ_UPDATED
N_OLCC = D.get("olcc_active_onprem") or 0
N_OLCC_FULL = D.get("olcc_active_full") or 0
CITIES, CUISINES, COUNTIES = D["cities"], D["cuisines"], D["counties"]
CART, BREWPUB, SEAFOOD, MARION, WINE, DONUT, TAQUERIA, OLDEST = 1, 2, 4, 8, 16, 32, 64, 128
HC_TAGS = CART | SEAFOOD | MARION | WINE | DONUT | TAQUERIA | OLDEST   # the hand-checked guides (brewpubs come from OLCC)
MI = ["", "MICHELIN Recommended", "Bib Gourmand", "1 MICHELIN Star", "2 MICHELIN Stars", "3 MICHELIN Stars"]   # Oregon: never set
OLCC_DATA = "https://data.oregon.gov/Business/Liquor-Business-Licenses-Endorsements/srxe-qkm2"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def hdate(iso):
    """2026-09-24 -> September 24, 2026"""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{MONTHS[int(m[2]) - 1]} {int(m[3])}, {m[1]}" if m else str(iso or "")


def hmonth(iso):
    m = re.match(r"(\d{4})-(\d{2})", str(iso or ""))
    return f"{MONTHS[int(m[2]) - 1]} {m[1]}" if m else str(iso or "")


def plural(n, one, many=None):
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def words_num(n):
    return NUM_WORDS[n] if 0 <= n < len(NUM_WORDS) else f"{n:,}"


def safe_url(u):
    """Only http(s) links leave the site; a bare host ("example.com/menu") gets https://. Anything else is dropped."""
    u = str(u or "").strip()
    if re.fullmatch(r"https?://[^\s\"'<>\\]+", u, re.I):
        return u
    if re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}(?:[/?#][^\s\"'<>\\]*)?", u, re.I):
        return "https://" + u
    return ""


# Websites we must not link (pipeline/website_blocklist.json): hacked, expired or another business's site. A blocked link is
# dropped, never the place. qa-site.py fails if a blocked domain or URL appears anywhere in docs/.
BLOCKLIST = json.load(open(f"{ROOT}/pipeline/website_blocklist.json"))
for _b in BLOCKLIST:
    assert _b.get("match", "domain") in ("domain", "url") and (_b.get("url") or _b.get("domain")), f"bad blocklist entry {_b}"
BLOCKED_LINKS = []   # (place, link) pairs the blocklist dropped from this build


def url_key(u):
    """A URL compared without its scheme, a leading www., a trailing slash or letter case."""
    return re.sub(r"^(?:https?:)?//(?:www\.)?", "", str(u or "").strip().lower()).rstrip("/")


def blocked_site(u):
    host = (urllib.parse.urlsplit(u).hostname or "").rstrip(".").removeprefix("www.")
    for b in BLOCKLIST:
        if b.get("match", "domain") == "url":
            if url_key(u) == url_key(b.get("url") or b["domain"]):
                return b
        else:
            d = b["domain"].strip().lower().rstrip(".").removeprefix("www.")
            if host == d or host.endswith("." + d):
                return b
    return None


class P:
    """One place, with the same meaning the app gives each field (OregonEats/Models/Place.swift)."""

    def __init__(self, r):
        self.r = r
        self.name = str(r["n"])
        self.city = CITIES[r["c"]] if r.get("c") is not None else ""
        self.county = COUNTIES[r["co"]] if r.get("co") is not None else None
        self.cuisine = CUISINES[r["cu"]] if r.get("cu") is not None else ""
        self.addr = (r.get("a") or "").strip().rstrip(",").strip()
        self.zip = str(r.get("z") or "")
        self.lat, self.lon = r.get("la"), r.get("lo")
        self.tags = r.get("g") or 0
        self.chain = (r.get("ch") or 0) >= 5
        self.venue = r.get("v") == 1
        self.ip = r.get("ip")
        self.founded = r.get("f") if isinstance(r.get("f"), int) else None
        self.fn = r.get("fn") or ""
        self.dishes = (r.get("dish") or "").replace("; ", ", ")
        self.season = r.get("seas") or ""
        self.note = r.get("note") or ""
        self.site = safe_url(r.get("w"))
        if self.site and blocked_site(self.site):
            BLOCKED_LINKS.append((self.name, self.site))
            self.site = ""   # the link goes, the place stays
        self.jbf = r.get("jbf") or ""
        self.h = r.get("h") or 0
        self.mi = r.get("mi") if r.get("mi") in range(1, len(MI)) else 0
        self.hc = r.get("hc") == 1   # hand-checked (a 2025-26 source, or an older one plus a 2026 OLCC license); the themed guides list only these
        self.lic = r.get("lic") or []   # official records: [[source, license number, type, expiration date]]

    def featured_key(self):
        # the app's "Featured first": honored places, then documented founding year, then name
        return (-(self.ip if self.ip is not None else -1), self.founded or 9999, self.name.lower())

    def jb_label(self):
        return ("America's Classic" if self.h & 1 else "James Beard winner" if self.h & 2 else "James Beard finalist" if self.h & 4
                else "James Beard semifinalist" if self.h & 8 else None)

    def promo_ok(self):
        """Any place may be named in a promotional spot: Oregon publishes no inspection results, so none can be a failed one."""
        return True

    def in_guide(self, tag):
        # brewpubs come from OLCC's Brewery Public House license; every other guide lists only hand-checked places
        return bool(self.tags & tag) and (self.hc or tag == BREWPUB)


PLACES = [P(r) for r in RECS]
REST = [p for p in PLACES if not p.venue]

ALL_GUIDES = [("cart", CART), ("brewpub", BREWPUB), ("seafood", SEAFOOD), ("donut", DONUT), ("wine", WINE), ("taqueria", TAQUERIA),
              ("marion", MARION)]
MIN_GUIDE = 4   # a guide gets its own page once its research has this many places (Idaho's rule); until then it's only in the web app
L_ALL = {k: sorted([p for p in REST if p.in_guide(t)], key=P.featured_key) for k, t in ALL_GUIDES}
GUIDE_TAGS = [(k, t) for k, t in ALL_GUIDES if len(L_ALL[k]) >= MIN_GUIDE]
L = {k: L_ALL[k] for k, _ in GUIDE_TAGS}
HON_L = sorted([p for p in REST if p.jbf], key=P.featured_key)
OLD_L = sorted([p for p in REST if p.founded and p.in_guide(OLDEST)], key=lambda p: (p.founded, p.name.lower()))
HAS_OLD = len(OLD_L) >= MIN_GUIDE
HC_ANY = [p for p in REST if p.hc and (p.tags & HC_TAGS)]   # on at least one hand-checked guide

# ---------------------------------------------------------------- regions: the app's six (by county)
REGIONS = list(D.get("regions") or [])
REGION_NAME = {r: r for r in REGIONS}
REGION_ORDER = ["Portland Metro", "Willamette Valley", "Oregon Coast", "Central Oregon", "Southern Oregon", "Gorge & Eastern Oregon"]
assert set(REGION_ORDER) == set(REGIONS), REGIONS
for p in PLACES:
    rg = p.r.get("rg")
    p.region = REGIONS[rg] if isinstance(rg, int) and 0 <= rg < len(REGIONS) else None


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- html helpers
e = html.escape


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("'", "").replace("&", "and")).strip("-")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def join_words(xs, conj="and"):
    xs = [x for x in xs if x]
    if len(xs) <= 1:
        return "".join(xs)
    return ", ".join(xs[:-1]) + f" {conj} " + xs[-1]


def fit(cands, lo, hi, what=""):
    seen = []
    # a description that misses the window by a few characters gets a fixed tail (state counts vary from build to build)
    more = [c.rstrip(".") + t for c in cands for t in (", with addresses and websites.", ". Free iPhone app coming soon.", ", with addresses.",
                                                         ". Free iPhone app.", ", with maps.")] if lo >= 100 else []
    for o in list(cands) + more:
        if lo <= len(o) <= hi:
            return o
        seen.append(o)
    raise ValueError(f"nothing fits {lo}-{hi} for {what}: {[(len(o), o) for o in seen[:12]]}")


# The app icon in miniature (scripts/make-brand.swift, same geometry): a slice of marionberry pie on marionberry plum.
LOGO = ('<svg viewBox="0 0 64 64" width="30" height="30" aria-hidden="true"><defs><clipPath id="lg-r"><rect width="64" height="64" rx="14"/></clipPath></defs>'
        '<g clip-path="url(#lg-r)"><rect width="64" height="64" fill="#5A1F46"/>'
        '<path d="M8.96 30.72H51.2V21.12Z" fill="#E0A95E"/>'
        '<rect x="8.96" y="40.64" width="42.24" height="3.52" fill="#A8622A"/>'
        '<rect x="8.96" y="32.64" width="42.24" height="8" fill="#7A2E62"/>'
        '<rect x="8.96" y="30.72" width="42.24" height="1.92" fill="#C98A3E"/>'
        '<rect x="48.96" y="19.52" width="6.08" height="24.64" rx="2.88" fill="#C98A3E"/>'
        '<path d="M26.88 28.48H32M35.84 27.84H42.24M38.4 24.64H44.8" stroke="#7A2E62" stroke-width="2.18" stroke-linecap="round"/></g></svg>')
FAVICON = "data:image/svg+xml," + LOGO.replace('width="30" height="30" ', "").replace(' aria-hidden="true"', "").replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ").replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")

# Nick's palette (2026-10-24): Oregon's official state colors (ORS 186.010), navy #14305C for text and accents (13.1:1 on white) and gold
# #F2B705 only as a fill under navy text (7.2:1; gold text on white fails AA), Crater Lake blue #1F5A96 for links in the stripe, and
# marionberry plum #5A1F46 (the icon's ground) for the headline's hard shadow; a warm cream #F7F3EA as the page tint. Lettering:
# condensed heavy system faces for headings, the system monospaced face for numbers; no web fonts are loaded (the CSP allows only this
# site, and the site loads nothing from anyone else).
CSS = """
  :root {
    --bg: #f7f3ea; --surface: #fff; --surface2: #eef1f6; --rule: #dde3eb;
    --ink: #0e1b2e; --ink2: #26364f; --muted: #556275;
    --accent: #14305c; --accent2: #1f5a96; --on-accent: #fff; --orange: #f2b705; --on-orange: #14305c; --plum: #5a1f46; --lime: #fcefc2; --soft: #e3eaf4; --limesoft: #fdf6dd;
    --focus: #1f5a96;
    --radius: 16px;
    --display: "Avenir Next Condensed", "Helvetica Neue Condensed", "Roboto Condensed", "Arial Narrow", system-ui, sans-serif; --head-font: "Caprasimo", "Avenir Next Condensed", "Helvetica Neue Condensed", "Roboto Condensed", "Arial Narrow", system-ui, sans-serif;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #0b1626; --surface: #112038; --surface2: #172a46; --rule: #253c5c; --ink: #eef3fa; --ink2: #d3ddeb; --muted: #a8b6c8; --accent: #a9c4ef; --accent2: #c7daf6; --on-accent: #0b1626; --plum: #7a2e62; --focus: #a9c4ef; }
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  @media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  a { color: var(--accent); text-underline-offset: 2px; }
  a:focus-visible, summary:focus-visible, button:focus-visible, select:focus-visible, input:focus-visible, [tabindex]:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; border-radius: 6px; }
  .skip { position: absolute; left: -9999px; top: 0; background: var(--orange); color: var(--on-orange); padding: 10px 14px; font-weight: 700; z-index: 10; }
  .skip:focus { left: 8px; top: 8px; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
  header.site { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 18px 0 14px; }
  .stripes { display: grid; grid-template-rows: 8px 5px 8px; margin: 0 0 4px; border-radius: 4px; overflow: hidden; }
  .stripes i { display: block; }
  .stripes i:nth-child(1) { background: #14305c; }
  .stripes i:nth-child(2) { background: #f2b705; }
  .stripes i:nth-child(3) { background: #2e5e4e; }
  .logo { display: flex; align-items: center; gap: 10px; font: 400 23px/1 var(--head-font); letter-spacing: .01em; color: var(--accent); text-decoration: none; }
  .logo svg { flex: 0 0 auto; border-radius: 7px; }
  header.site nav { display: flex; flex-wrap: wrap; gap: 4px 16px; justify-content: flex-end; }
  header.site nav a { color: var(--ink2); text-decoration: none; font-size: 15px; }
  header.site nav a:hover { color: var(--accent); text-decoration: underline; }
  h1, h2 { font-family: var(--head-font); font-weight: 400; color: var(--accent); letter-spacing: -.005em; }
  h1 { font-size: clamp(40px, 12.5vw, 64px); line-height: 1.08; margin: 0 0 18px; overflow-wrap: break-word; text-wrap: balance; }
  .kicker { font: 600 13px/1.4 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--accent); margin: 0 0 12px; }
  .kicker::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--orange); margin: 0 8px 1px 0; }
  h2 { font-size: 32px; line-height: 1.02; margin: 0 0 10px; }
  h3 { font-size: 18px; margin: 0; line-height: 1.3; }
  .lede { font-size: 19px; color: var(--ink2); margin: 0 0 26px; }
  .hero { padding: 44px 0 28px; }
  section { padding: 36px 0; border-top: 1px solid var(--rule); }
  section.hero { border: 0; }
  .sub { color: var(--ink2); margin: 0 0 22px; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .btn { display: inline-flex; align-items: center; gap: 10px; background: var(--orange); color: var(--on-orange); font-weight: 700; padding: 14px 20px; border-radius: 14px; text-decoration: none; font-size: 17px; }
  .btn-ghost { background: transparent; color: var(--accent); border: 2px solid var(--accent); }
  .pill { font-size: 14px; color: var(--muted); }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 28px 0 0; padding: 0; list-style: none; }
  .stats li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px; }
  .stats b { display: block; font: 600 28px/1 var(--mono); color: var(--accent); }
  .stats span { font-size: 14px; color: var(--muted); }
  .steps { display: grid; gap: 12px; list-style: none; margin: 0; padding: 0; }
  .step { display: flex; gap: 14px; background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .step .n { flex: 0 0 32px; height: 32px; border-radius: 50%; background: var(--orange); color: var(--on-orange); font-weight: 800; display: grid; place-items: center; }
  .step p { margin: 4px 0 0; color: var(--ink2); }
  .shots { display: flex; gap: 14px; overflow-x: auto; margin: 0 -20px; padding: 4px 20px 14px; scroll-snap-type: x proximity; list-style: none; }
  .shots li { flex: 0 0 auto; width: 210px; scroll-snap-align: start; }
  .shots img { display: block; width: 210px; height: auto; border-radius: 24px; border: 1px solid var(--rule); background: var(--surface2); }
  .shots p { font-size: 14px; color: var(--muted); margin: 8px 2px 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .card { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .card h3 { font: 400 20px/1.1 var(--head-font); letter-spacing: .01em; }
  a.card.gc { display: flex; flex-direction: column; gap: 6px; border: 0; border-radius: 18px; min-height: 150px; }
  a.card.gc b { font: 600 32px/1 var(--mono); margin-bottom: auto; }
  a.card.gc p, a.card.gc h3 { color: inherit; }
  a.card.gc p { opacity: .92; }
  a.card.gc.gc-cart, a.card.gc.gc-brewpub, a.card.gc.gc-seafood, a.card.gc.gc-marion, a.card.gc.gc-wine, a.card.gc.gc-donut, a.card.gc.gc-taqueria { background: #f2b705; color: #14305c; }
  a.card.gc.gc-oldest, a.card.gc.gc-honors { background: #14305c; color: #fff; }
  .card p { margin: 6px 0 0; color: var(--ink2); }
  a.card { display: block; text-decoration: none; color: var(--ink); }
  a.card:hover h3 { text-decoration: underline; color: var(--accent); }
  .cities { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin: 0; }
  .cities a { display: inline-block; padding: 8px 12px; border-radius: 999px; border: 1px solid var(--rule); background: var(--surface); text-decoration: none; color: var(--ink); font-size: 15px; }
  .cities a:hover { border-color: var(--accent); }
  .cities a[aria-current] { border-color: var(--accent); font-weight: 700; }
  details { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 2px 18px; margin-bottom: 10px; }
  summary { cursor: pointer; padding: 14px 0; font-weight: 600; list-style: none; display: flex; justify-content: space-between; gap: 12px; }
  summary::-webkit-details-marker { display: none; }
  summary::after { content: "+"; color: var(--accent); font-weight: 800; }
  details[open] summary::after { content: "\\2013"; }
  details p { margin: 0 0 16px; color: var(--ink2); }
  .final { text-align: center; }
  .final .cta-row { justify-content: center; }
  nav.crumbs { font-size: 14px; color: var(--muted); padding: 16px 0 0; }
  nav.crumbs ol { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
  nav.crumbs li + li::before { content: "/"; margin-right: 6px; color: var(--rule); }
  nav.crumbs a { color: var(--muted); }
  .places { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
  .places li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px 16px; min-width: 0; overflow-wrap: anywhere; scroll-margin-top: 12px; }
  .places li:target { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
  .places .where { margin: 2px 0 0; font-size: 15px; color: var(--muted); }
  .places .facts { margin: 8px 0 0; font-size: 15px; color: var(--ink2); }
  .places .facts b { color: var(--ink); font-weight: 600; }
  .places .note { margin: 6px 0 0; font-size: 15px; color: var(--ink2); }
  .places .fine { margin: 6px 0 0; }
  .places .link { font-size: 14px; margin: 6px 0 0; }
  .tag { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; background: var(--lime); color: #0e1b2e; border-radius: 6px; padding: 1px 6px; margin: 0 4px 2px 0; }
  .tag-mi { background: #5a1f46; color: #fff; }
  .tag-jb { background: #14305c; color: #fff; }
  .tag-plain { background: var(--soft); color: #0e1b2e; }
  .toc { columns: 2; padding-left: 20px; margin: 0; }
  table { border-collapse: collapse; width: 100%; font-size: 15px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--rule); vertical-align: top; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  .tbl { overflow-x: auto; }
  .res { display: inline-block; font: 800 12px/1.4 -apple-system, system-ui, sans-serif; letter-spacing: .04em; text-transform: uppercase; padding: 2px 6px; border-radius: 6px; }
  .res-ok { background: #ddefe3; color: #0e5a2b; } .res-mid { background: #ffe9c2; color: #6b3a00; } .res-low { background: #f9d5db; color: #7a0019; }
  .groups { list-style: none; padding: 0; margin: 0 0 18px; display: grid; gap: 12px; }
  .groups > li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px 16px; }
  .groups ul { margin: 8px 0 0; padding-left: 20px; color: var(--ink2); font-size: 15px; }
  .groups .count { margin: 8px 0 0; font-weight: 600; }
  .fine { font-size: 14px; color: var(--muted); }
  .legal h2 { font-size: 26px; margin-top: 28px; }
  .legal p, .legal li { color: var(--ink2); }
  footer { padding: 32px 0 56px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--rule); margin-top: 20px; }
  footer nav { display: flex; flex-wrap: wrap; gap: 8px 16px; }
  footer a { color: var(--muted); }
  footer p { margin: 12px 0 0; }
  @media (max-width: 600px) {
    .grid2 { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr 1fr; }
    .toc { columns: 1; }
    .toc a { display: inline-block; padding: 3px 0; }
    header.site { flex-direction: column; align-items: flex-start; }
    header.site nav { justify-content: flex-start; }
    header.site nav a, footer nav a, nav.crumbs a { display: inline-block; padding: 10px 0; }
    footer nav { gap: 0 18px; }
    th, td { padding: 8px 4px; font-size: 14px; }
    .tbl th, .tbl td { padding: 8px 3px; font-size: 13px; }
    .res { font-size: 11px; letter-spacing: .02em; padding: 2px 4px; }
    nav.crumbs ol { align-items: center; }
  }
"""

# The headline face: Caprasimo (SIL Open Font License, in docs/fonts/OFL-Caprasimo.txt). It is the site's one web font and it is served from this
# site, so pages still load nothing from anyone else. The big headline, the section headings, card titles and the site name use it
# (--head-font); numbers and badges keep the condensed system faces (--display).
CSS = "".join(f'  @font-face {{ font-family: "Caprasimo"; src: url("{BASE}/fonts/{_f}") format("woff2"); font-weight: 400; font-style: normal; font-display: swap; unicode-range: {_r}; }}\n'
              for _f, _r in (
                  ("caprasimo-latin-ext.woff2", "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF"),
                  ("caprasimo-latin.woff2", "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"),
              )) + CSS


def jsonld(obj):
    big = obj.get("@type") == "ItemList"
    raw = json.dumps(obj, ensure_ascii=False, indent=None if big else 1, separators=(",", ":") if big else None)
    return '<script type="application/ld+json">\n' + raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026") + "\n</script>"


def crumbs(trail):
    """trail: [(name, url)] ending with the current page."""
    items = "".join(f'<li><a href="{u}">{e(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{e(n)}</li>'
                    for i, (n, u) in enumerate(trail))
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(trail)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>', ld


def store_button(label="Ask for early access"):
    # A plain mailto button until launch: no Apple logo (Apple's marketing rules allow it only in the official badge). When
    # APP_STORE_URL is set in page() below, swap this for Apple's "Download on the App Store" badge artwork. Only Nick's internal
    # TestFlight group exists (2026-10-13): the mailto asks, and no page copy promises an invite or a link.
    return (f'<a class="btn store-btn" href="mailto:{EMAIL}?subject=Oregon%20Eats%20early%20access&amp;body=Send%20me%20the%20TestFlight%20link.">'
            f'<span class="store-label">{label}</span></a>')


STORE_NOTE = "The free Oregon Eats app for iPhone and iPad is on its way to the App Store."


def sha256_src(s):
    return "'sha256-" + base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode() + "'"


def csp_for(doc):
    """A strict policy for one finished page: only its own inline <script>/<style> blocks (by hash), same-origin data and images."""
    scripts = re.findall(r"<script>(.*?)</script>", doc, re.S)          # executable inline scripts (JSON-LD blocks are data, not run)
    styles = re.findall(r"<style>(.*?)</style>", doc, re.S)
    return ("default-src 'none'; "
            f"script-src {' '.join(sha256_src(s) for s in scripts) or chr(39) + 'none' + chr(39)}; "
            f"style-src {' '.join(sha256_src(s) for s in styles) or chr(39) + 'none' + chr(39)}; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'")


CSP_SLOT = "__CSP__"
written, noindexed = [], []
NAV = [("/oregon-food-carts.html", "Food carts"), ("/oregon-brewpubs.html", "Brewpubs"), ("/oregon-coast-seafood.html", "Coast seafood"),
       ("/cities/", "Cities"), ("/explore/", "Search")]


def page(path, title, desc, body, lds=(), robots="index,follow,max-image-preview:large", og_alt=None, extra_css="", og_type="article"):
    assert 50 <= len(title) <= 60 or path == "404.html", (path, len(title), title)
    assert 140 <= len(desc) <= 160 or path == "404.html", (path, len(desc), desc)
    assert body.count("<h1") == 1, path
    assert 'style="' not in body, f"{path}: inline style attributes break the CSP"
    url = DOMAIN + "/" + ("" if path == "index.html" else path.removesuffix("index.html"))
    indexed = "noindex" not in robots
    if not any("parentOrganization" in json.dumps(x) for x in lds):   # every page names its publisher and the Eats Ranked parent
        lds = list(lds) + [{"@context": "https://schema.org", **ORG_REF}]
    og_alt = og_alt or f"{BRAND}: {TAGLINE}. Oregon restaurants, with hand-checked food carts, coast seafood and doughnut shops."
    ld = "\n".join(jsonld(x) for x in lds)
    canon = f'<link rel="canonical" href="{url}">\n' if indexed else ""
    og_url = f'<meta property="og:url" content="{url}">\n' if indexed else ""
    nav = "\n".join(f'      <a href="{u}">{t}</a>' for u, t in NAV)
    doc = f"""<!DOCTYPE html>
<html lang="en" data-base="{BASE}">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{CSP_SLOT}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{canon}<meta name="robots" content="{robots}">
<meta name="theme-color" content="#14305c">
<!-- Smart App Banner: once the App Store Connect record exists, replace APP_ID with the numeric Apple ID and uncomment.
<meta name="apple-itunes-app" content="app-id=APP_ID">
-->
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
{og_url}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/og.png">
<link rel="icon" type="image/svg+xml" href="{FAVICON}">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="preload" href="/fonts/caprasimo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="manifest" href="/site.webmanifest">
<style>{CSS}{extra_css}</style>
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <header class="site">
    <a class="logo" href="/" aria-label="{BRAND} home">{LOGO}{BRAND}</a>
    <nav aria-label="Main">
{nav}
    </nav>
  </header>
  <div class="stripes" aria-hidden="true"><i></i><i></i><i></i></div>
{body}
  <footer>
    <nav aria-label="Footer">
      <a href="/">{BRAND} app</a>
      <a href="/explore/">Search Oregon restaurants</a>
{chr(10).join(f'      <a href="{u}">{e(t)}</a>' for u, t in GUIDE_LINKS)}
      <a href="/cities/">Cities and towns</a>
      <a href="/privacy.html">Privacy policy</a>
      <a href="/terms.html">Terms of use</a>
      <a href="mailto:{EMAIL}">Email us</a>
    </nav>
    <p>{SOURCES_LINE}</p>
    <p>© 2026 {BRAND}. Part of <a href="{HUB['url']}" rel="noopener">Eats Ranked</a>, restaurant apps state by state.</p>
    <p>Created by <a href="https://work-with-nick.com/" rel="author">Nick Soderstrom</a>.</p>
  </footer>
</div>
<script>
  // Once the App Store listing exists, paste its URL here (looks like https://apps.apple.com/app/id123456789).
  // Every button switches from "Ask for early access" to "Download on the App Store" automatically (then use Apple's badge artwork,
  // see store_button() in scripts/make-site.py). Also fill in the apple-itunes-app meta tag in <head> on every page, and put the
  // MobileApplication "offers" back in the landing page's JSON-LD (re-run scripts/make-site.py after editing it there).
  var APP_STORE_URL = "";
  if (APP_STORE_URL) {{
    document.querySelectorAll(".store-btn").forEach(function (b) {{ b.href = APP_STORE_URL; b.rel = "noopener"; }});
    document.querySelectorAll(".store-label").forEach(function (l) {{ l.textContent = "Download on the App Store"; }});
    document.querySelectorAll(".store-note").forEach(function (n) {{ n.textContent = "Free for iPhone and iPad."; }});
  }}
</script>
</body>
</html>
"""
    if BASE:   # served under /oregon-eats/: every root-relative link and asset gets the prefix
        doc = re.sub(r'(href|src|srcset)="/', rf'\1="{BASE}/', doc)
    doc = doc.replace(CSP_SLOT, csp_for(doc), 1)   # hashed last, over the exact bytes the browser will see
    os.makedirs(os.path.dirname(f"{DOCS}/{path}"), exist_ok=True)
    open(f"{DOCS}/{path}", "w").write(doc)
    (written if indexed else noindexed).append(path)
    return path


class Anchors:
    """Gives each place an id (name-zip) the first time it appears on a page, so ItemList items can point to page#id."""
    RESERVED = {"main", "about", "list", "honors", "oldest", "inspections", "cuisines", "more", "towns", "how", "what", "guides", "cities",
                "faq", "download", "screens", "pricing", "privacy", "groups", "counties", "lookup", "closures", "tiers", "lg-r", "lg-f", "lg-p",
                "cities-list", "alcohol"} | {k for k, _ in ALL_GUIDES}

    def __init__(self, page_url):
        self.page_url, self.used, self.of = page_url, set(self.RESERVED), {}

    def take(self, p):
        if id(p) in self.of:
            return None
        base = slug(p.name + (" " + p.zip if p.zip else "")) or "place"
        a, n = base, 2
        while a in self.used:
            a, n = f"{base}-{n}", n + 1
        self.used.add(a)
        self.of[id(p)] = a
        return a

    def url(self, p):
        return f"{self.page_url}#{self.of[id(p)]}"


CHIPS = [(CART, "Food cart"), (BREWPUB, "Brewpub"), (SEAFOOD, "Coast seafood"), (MARION, "Marionberry pie"), (WINE, "Wine country"),
         (DONUT, "Doughnuts"), (TAQUERIA, "Taquería")]


def place_item(p, anchors=None, show_fn=False, honors=False):
    facts = []
    if p.dishes:
        facts.append(f"<b>On the menu:</b> {e(p.dishes)}")
    if p.founded:
        facts.append(f"<b>Since</b> {e(str(p.founded))}")
    if p.season:
        facts.append(f"<b>Season:</b> {e(p.season)}")
    kinds = []
    if p.mi:
        kinds.append(('<span class="tag tag-mi">', e(MI[p.mi])))
    if p.jb_label():
        kinds.append(('<span class="tag tag-jb">', e(p.jb_label())))
    kinds += [('<span class="tag">', k) for t, k in CHIPS if p.tags & t and (p.hc or t == BREWPUB)]
    where = ", ".join(x for x in (p.addr, p.city) if x)
    aid = anchors.take(p) if anchors else None
    out = [f'<li id="{e(aid)}">' if aid else "<li>", f"<h3>{e(p.name)}</h3>", f'<p class="where">{e(where)}</p>']
    if kinds or facts:
        out.append('<p class="facts">' + "".join(f"{tag}{k}</span>" for tag, k in kinds) + (" " + " · ".join(facts) if facts else "") + "</p>")
    if p.note:
        out.append(f'<p class="note">{e(p.note)}</p>')
    if show_fn and p.fn:
        out.append(f'<p class="fine">{e(p.fn)}</p>')
    if honors and p.jbf:   # restaurateur-level honors have no chip, so say what the honor is
        out.append('<p class="fine">' + e("; ".join("James Beard: " + x for x in p.jbf.split("; "))) + "</p>")
    if p.site:
        host = re.sub(r"^https?://(www\.)?", "", p.site, flags=re.I).split("/")[0]
        out.append(f'<p class="link"><a href="{e(p.site)}" rel="noopener nofollow">{e(host)}</a></p>')
    out.append("</li>")
    return "".join(out)


def restaurant_ld(p, item_url):
    addr = {"@type": "PostalAddress"}
    if p.addr:
        addr["streetAddress"] = p.addr
    if p.city:
        addr["addressLocality"] = p.city
    addr["addressRegion"] = "OR"
    if p.zip:
        addr["postalCode"] = p.zip
    addr["addressCountry"] = "US"
    x = {"@type": "Restaurant", "name": p.name, "url": item_url, "address": addr}
    if p.lat is not None and p.lon is not None:
        x["geo"] = {"@type": "GeoCoordinates", "latitude": p.lat, "longitude": p.lon}
    if p.site:
        x["sameAs"] = p.site
    if p.founded:
        x["foundingDate"] = str(p.founded)
    if p.cuisine and p.cuisine not in ("Other", "Restaurant", "American & Other"):
        x["servesCuisine"] = p.cuisine
    return x


def item_list(name, places, url, anchors):
    """An all-on-one-page list: each item's url is its anchor on this page; the restaurant's own site goes in sameAs."""
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "url": url, "numberOfItems": len(places),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": restaurant_ld(p, anchors.url(p))} for i, p in enumerate(places)]}


def article_ld(url, headline, desc):
    return {"@context": "https://schema.org", "@type": "Article", "headline": headline, "description": desc,
            "datePublished": PUBLISHED, "dateModified": TODAY, "inLanguage": "en", "mainEntityOfPage": url,
            "image": f"{DOMAIN}/og.png", "author": ORG_REF, "publisher": ORG_REF}


# ---------------------------------------------------------------- counts shared by several pages
N_REST = len(REST)
N_TOWNS = len({p.city for p in REST if p.city})
N_COUNTIES = len({p.county for p in REST if p.county})
N_OFFICIAL = sum(1 for p in REST if p.r.get("t") == 2)
N_LIQ = sum(1 for p in REST if p.r.get("liq") == 1)
N_HC = len(HC_ANY)
N_JBF = sum(1 for p in HON_L if p.jbf)
N_CLASSICS = sum(1 for p in HON_L if p.h & 1)
INS_PATH = "oregon-restaurant-inspections.html"
HON_PATH = "oregon-james-beard-restaurants.html"
OLD_PATH = "oregon-oldest-restaurants.html"
GUIDE_PATH = {"cart": "oregon-food-carts.html", "brewpub": "oregon-brewpubs.html", "seafood": "oregon-coast-seafood.html",
              "donut": "oregon-doughnut-shops.html", "wine": "willamette-valley-wine-country-restaurants.html", "taqueria": "oregon-taquerias.html",
              "marion": "oregon-marionberry-pie.html"}
GUIDE_NAME = {"cart": "Food carts", "brewpub": "Brewpubs", "seafood": "Coast seafood", "donut": "Doughnut shops", "wine": "Wine country",
              "taqueria": "Taquerías", "marion": "Marionberry pie"}
GUIDE_LINKS = ([("/" + GUIDE_PATH[k], GUIDE_NAME[k]) for k, _ in GUIDE_TAGS]
               + ([("/" + OLD_PATH, "Oldest restaurants")] if HAS_OLD else [])
               + [("/" + HON_PATH, "James Beard honors"), ("/" + INS_PATH, "Oregon restaurant inspections")])
for _k in ("cart", "brewpub", "seafood"):   # the header nav links these three pages
    assert _k in L, f"the {_k} guide has fewer than {MIN_GUIDE} places: fix NAV"

SOURCES_LINE = (f"Place data: hand-checked research by {BRAND} ({CHECKED}); the Oregon Liquor and Cannabis Commission's liquor license list "
                "(data.oregon.gov); Overture Maps Foundation places (CDLA Permissive 2.0); map outlines © OpenStreetMap contributors, Overture "
                "Maps Foundation (ODbL). Not affiliated with or endorsed by the State of Oregon, OLCC, the Oregon Health Authority, any county "
                "health department, Travel Oregon, any restaurant or chain, or the James Beard Foundation. James Beard Foundation and James Beard "
                "Award are trademarks of the James Beard Foundation. Places open and close, so check before you go.")


def by_region(places, key=lambda p: (p.city, p.name.lower())):
    groups = defaultdict(list)
    for p in places:
        groups[p.region or "Elsewhere"].append(p)
    order = REGION_ORDER + ["Elsewhere"]
    return [(REGION_NAME.get(r, "Elsewhere in Oregon"), sorted(groups[r], key=key)) for r in order if groups.get(r)]


def region_sections(places, noun, plural_noun, anchors, **item_kw):
    toc = '<ul class="toc">' + "".join(f'<li><a href="#{slug(r)}">{e(r)}</a> ({len(ps)})</li>' for r, ps in by_region(places)) + "</ul>"
    secs = []
    for r, ps in by_region(places):
        anchors.used.update({slug(r), "h-" + slug(r)})
        secs.append(f'<section id="{slug(r)}" aria-labelledby="h-{slug(r)}"><h2 id="h-{slug(r)}">{e(r)}</h2>'
                    f'<p class="sub">{plural(len(ps), noun, plural_noun)}, by town.</p><ol class="places">'
                    + "".join(place_item(p, anchors, **item_kw) for p in ps) + "</ol></section>")
    return toc, "\n".join(secs)


# ---------------------------------------------------------------- city pages: which towns get one
CITY_WANTED = ["Portland", "Bend", "Eugene", "Salem", "Newport", "Astoria", "McMinnville", "Newberg", "Springfield", "Medford", "Ashland",
               "Hood River", "Corvallis", "Hillsboro", "Beaverton", "Lincoln City", "Seaside", "Woodburn"]
MIN_LISTED = 5   # hand-checked, licensed-brewpub, honored or oldest places in the town itself: fewer, and the town gets no page yet


def town_listed(c):
    return [p for p in REST if p.city == c and ((p.hc and p.tags & HC_TAGS) or p.tags & BREWPUB or p.mi or p.jbf)]


CITY_PAGES = [c for c in CITY_WANTED if any(p.city == c and p.lat is not None for p in REST) and len(town_listed(c)) >= MIN_LISTED]
CITY_SKIPPED = {c: len(town_listed(c)) for c in CITY_WANTED if c not in CITY_PAGES}


def city_url(c):
    return f"/cities/{slug(c)}.html"


def city_links(current=None):
    return '<ul class="cities">' + "".join(f'<li><a href="{city_url(c)}"{" aria-current=" + chr(34) + "page" + chr(34) if c == current else ""}>{e(c)}</a></li>'
                                           for c in CITY_PAGES) + "</ul>"


def other_guides(skip):
    return "Other guides: " + ", ".join(f'<a href="{u}">{e(t)}</a>' for u, t in GUIDE_LINKS if u != skip) + "."


def guide_page(path, h1, kicker, title_opts, desc_opts, lede, about_html, places, noun, plural_noun, list_name, region=True, **item_kw):
    url = f"{DOMAIN}/{path}"
    # counts are small or large enough that the written lengths can miss the 140-160 window: each option also gets fixed tails
    tails = (", with addresses and websites.", ", with each place's address and website.", ". Free iPhone app coming soon.", ", with addresses.",
             ". Free iPhone app.", ", with maps.")
    desc_opts = list(desc_opts) + [d.rstrip(".") + t for d in desc_opts for t in tails]
    title_opts = list(title_opts) + [t + f" | {BRAND}" for t in title_opts if BRAND not in t]
    title, desc = fit(title_opts, 50, 60, path + " title"), fit(desc_opts, 140, 160, path + " description")
    nav, bc = crumbs([("Home", "/"), (h1, "/" + path)])
    anchors = Anchors(url)
    if region:
        toc, secs = region_sections(places, noun, plural_noun, anchors, **item_kw)
        jump = f"<h2>Jump to a region</h2>\n    {toc}"
    else:
        secs = (f'<section id="list" aria-labelledby="h-list"><h2 id="h-list">Oldest first</h2><ol class="places">'
                f'{"".join(place_item(p, anchors, **item_kw) for p in places)}</ol></section>')
        jump = ""
    body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{kicker}</p>
    <h1>{e(h1)}</h1>
    <p class="lede">{lede}</p>
    <div class="cta-row">{store_button()}<span class="pill store-note">{STORE_NOTE}</span></div>
  </section>
  <section id="about">
    {about_html}
    <p class="fine">{other_guides("/" + path)} City pages: {", ".join(f'<a href="{city_url(c)}">{e(c)}</a>' for c in CITY_PAGES)}.</p>
    {jump}
  </section>
{secs}
  </main>"""
    page(path, title, desc, body, [article_ld(url, h1, desc), bc, item_list(list_name, places, url, anchors)])


def towns_text(places, k):
    return join_words([t for t, _ in Counter(p.city for p in places).most_common(k)])


def towns_counts(places, k=8):
    return ", ".join(f"{t} ({n})" for t, n in Counter(p.city for p in places).most_common(k))


def top_dishes(places, k=6, skip=()):
    c = Counter()
    for p in places:
        # sorted: a set's order changes from run to run, and ties in most_common() would reorder the copy on every rebuild
        for d in sorted({x.strip().lower() for x in re.split(r"[;,]", p.r.get("dish") or "") if x.strip()}):
            if d not in skip:
                c[d] += 1
    return ", ".join(f"{d} ({n})" for d, n in c.most_common(k) if n > 1)


HOW_BUILT = ("Our method: a place made the list only if a source named it and its street address matched our records. A dated 2025 or "
             "2026 page (local news, an official tourism listing or the place's own site) was enough; an older or undated page counted only "
             "when the place also held an active liquor license on the Oregon Liquor and Cannabis Commission's list in 2026. Review sites "
             "played no part, and places run by region and town rather than by anybody's score. Hours change, so check before you go.")
BREWPUB_HOW = (f"Our method: every place in our data matched to an active OLCC Brewery Public House license (read {hdate(LIC_UPDATED)}), one "
               "place per license, chosen by the license's trade name. Nothing here is hand-checked or ranked by a score, and a brewery that "
               "pours under another license type isn't on this list. Hours change, so check before you go.")
APP_LINE = (f"On your phone, {BRAND} orders this list by how far each place is from you, and a tap opens Apple Maps' live card with "
            "hours, photos and directions.")


def checked_kicker():
    return f"{BRAND} · checked by hand, {CHECKED}"


def seasonal_line(places):
    n = sum(1 for p in places if p.season)
    return f" {plural(n, 'place')} on this list {'notes a season' if n == 1 else 'note a season'}; seasonal is not closed." if n else ""


# ---------------------------------------------------------------- the themed guides
assert all(len(v) > 1 for v in L.values()), "the guide copy writes plural nouns"


def guide(k, h1, titles, descs, lede, about, list_name, noun="place"):
    G = L[k]
    plural_noun = noun[:-1] + "ies" if noun.endswith("y") and noun[-2] not in "aeiou" else noun + "s"
    official = k == "brewpub"   # from OLCC's license list, not hand-checked: its own kicker and method
    kicker = f"{BRAND} · from OLCC's license list, read {hdate(LIC_UPDATED)}" if official else checked_kicker()
    guide_page(GUIDE_PATH[k], h1, kicker, titles, descs, lede, about + f"""
    <h2>The list at a glance</h2>
    <p>Towns with the most: {e(towns_counts(G))}.{(" The dishes we found most often: " + e(top_dishes(G)) + ".") if top_dishes(G) else ""}</p>
    <p>{BREWPUB_HOW if official else HOW_BUILT}</p>
    <p>{APP_LINE}</p>""", G, noun, plural_noun, list_name)


GUIDE_DEFS = {
    "cart": ("Oregon food carts and pods",
             [lambda n: f"Oregon Food Carts & Pods: {n} Hand-Checked Places", lambda n: f"Portland, Bend & Eugene Food Carts: {n} Checked Places",
              lambda n: f"Food Carts in Oregon: {n} Checked Carts and Pods | {BRAND}"],
             [lambda n: f"{plural(n, 'food cart')} and cart pods in Portland, Bend, Eugene and Springfield, each confirmed at its pod in {CHECKED} against a 2026 source, by town.",
              lambda n: f"Oregon food carts: {plural(n, 'cart')} and pods, from Portland's Woodstock and Division lots to Bend and Eugene, each checked in {CHECKED}, by town."],
             lambda n: f"{plural(n, 'food cart')} and cart pods in Portland, Bend, Eugene and Springfield, each confirmed at its pod in {CHECKED} against a 2026 source. Carts move and close often, so check before you go.",
             """<h2>Lunch from a window</h2>
    <p>A pod is a lot ringed with food carts around shared tables, often with a beer cart or a bar. Portland's run from Woodstock to Alberta, and Bend and Eugene have lots with fire pits and taprooms. Oregon's county health departments inspect carts but don't score them, and carts change spots often: this list names each cart's pod as of 2026.</p>""",
             "Oregon food carts and pods", "place"),
    "brewpub": ("Oregon brewpubs",
                [lambda n: f"Oregon Brewpubs: {n} With a Brewery Public House License", lambda n: f"Oregon Brewpubs: {n} Licensed Brewery Pubs | {BRAND}",
                 lambda n: f"Brewpubs in Oregon: {n} State-Licensed Places | {BRAND}"],
                [lambda n: f"{plural(n, 'Oregon place')} with an active OLCC Brewery Public House license: breweries pouring their own beer with food, from Astoria to Ontario, by town.",
                 lambda n: f"Oregon brewpubs: {plural(n, 'place')} holding a Brewery Public House license from the state's liquor commission, by region and town."],
                lambda n: f"{plural(n, 'place')} in Oregon with an active Brewery Public House license from the Oregon Liquor and Cannabis Commission: breweries that pour their own beer and serve food on site.",
                """<h2>Straight from the license</h2>
    <p>OLCC's Brewery Public House license lets a brewery pour its own beer at a pub that serves food. This list comes from that license, not from a review or a reader poll: each place here holds one, matched to it by the license's trade name.</p>""",
                "Oregon brewpubs", "place"),
    "seafood": ("Oregon coast seafood",
                [lambda n: f"Oregon Coast Seafood: {n} Chowder, Crab & Oyster Spots", lambda n: f"Oregon Coast Chowder & Dungeness Crab: {n} Places",
                 lambda n: f"Oregon Coast Seafood: {n} Checked Places | {BRAND}"],
                [lambda n: f"{plural(n, 'Oregon coast restaurant')} for clam chowder, Dungeness crab and oysters, from Astoria to Port Orford, each checked in {CHECKED}, by town.",
                 lambda n: f"Oregon coast seafood: {plural(n, 'place')} for chowder, crab and Netarts and Coos Bay oysters, each checked in {CHECKED}, by region and town."],
                lambda n: f"{plural(n, 'place')} on the Oregon coast for clam chowder, Dungeness crab and oysters from Netarts, Tillamook and Coos bays, each checked in {CHECKED}.",
                """<h2>Chowder weather</h2>
    <p>Dungeness crab, clam chowder and bay oysters are the coast's everyday seafood: crab boats work out of Newport and Astoria, and oysters grow in Netarts, Tillamook, Yaquina and Coos bays. Many coast places keep shorter hours in winter.</p>""",
                "Oregon coast seafood restaurants", "place"),
    "donut": ("Oregon doughnut shops",
              [lambda n: f"Oregon Doughnut Shops: {n} Hand-Checked Places | {BRAND}", lambda n: f"Doughnut Shops in Oregon: {n} Checked Places",
               lambda n: f"Oregon Doughnuts: {n} Shops From Burns to Beaverton"],
              [lambda n: f"{plural(n, 'Oregon doughnut shop')}, from cake doughnuts in Sandy to mochi doughnuts in Central Point, each checked in {CHECKED} against a 2026 source, by town.",
               lambda n: f"Oregon doughnuts: {plural(n, 'shop')} statewide, classic, vegan and mochi, each checked in {CHECKED} against a 2026 source, by region and town."],
              lambda n: f"{plural(n, 'doughnut shop')} across Oregon, each checked in {CHECKED} against a 2026 source: classic cake and raised doughnuts, vegan doughnuts, mochi doughnuts and Japanese curry pan.",
              """<h2>From Burns to Beaverton</h2>
    <p>Oregon's doughnut shops run from a bakery in Burns and a doughnut company in Joseph to Portland's vegan and mochi-doughnut counters and a Japanese bakery's curry pan in Beaverton. This list is the independent shops; Portland's two best-known doughnut chains aren't on it.</p>""",
              "Oregon doughnut shops", "shop"),
    "wine": ("Willamette Valley wine country restaurants",
             [lambda n: f"Willamette Valley Wine Country Restaurants: {n} Checked", lambda n: f"Willamette Valley Wine Country Dining: {n} Restaurants",
              lambda n: f"Oregon Wine Country Restaurants: {n} Checked | {BRAND}"],
             [lambda n: f"{plural(n, 'restaurant')} in the Willamette Valley wine country, in Newberg, Dundee, Dayton and Carlton, each checked in {CHECKED}, by town.",
              lambda n: f"Willamette Valley wine country: {plural(n, 'dining room')} among the vineyards of Yamhill County, each checked in {CHECKED}, by town."],
             lambda n: f"{plural(n, 'restaurant')} in the Willamette Valley's wine country, in Newberg, Dundee, Dayton and Carlton, each checked in {CHECKED} against a tourism listing and an active 2026 liquor license.",
             """<h2>Among the vineyards</h2>
    <p>Yamhill County's small towns sit among the vineyards of the northern Willamette Valley, and their dining rooms cook for winemakers and the visitors touring the tasting rooms.</p>""",
             "Willamette Valley wine country restaurants", "restaurant"),
    "taqueria": ("Oregon taquerías",
                 [lambda n: f"Oregon Taquerías: {n} Hand-Checked Taco Spots | {BRAND}", lambda n: f"Taquerías in Oregon: {n} Checked Taco Places",
                  lambda n: f"Oregon Taquerias and Taco Carts: {n} Checked Places"],
                 [lambda n: f"{plural(n, 'Oregon taquería')} and taco cart, from Woodburn's Front Street to Hood River and Portland's carts, each checked in {CHECKED}, by town.",
                  lambda n: f"Oregon taquerías: {plural(n, 'place')} for tacos, from Woodburn and Hood River to Portland's taco carts, each checked in {CHECKED}, by town."],
                 lambda n: f"{plural(n, 'taquería')} and taco cart in Oregon, from Woodburn's Front Street and Hood River to Portland's carts, each checked in {CHECKED}.",
                 """<h2>Tortillas and trompo</h2>
    <p>Woodburn's Front Street and Hood River's taquerías feed the farm country around them, and in Portland the carts cook Mexico City tacos de canasta and Yucatecan panuchos.</p>""",
                 "Oregon taquerías", "place"),
    "marion": ("Oregon marionberry pie",
               [lambda n: f"Marionberry Pie in Oregon: {n} Hand-Checked Places", lambda n: f"Oregon Marionberry Pie: {n} Checked Places | {BRAND}"],
               [lambda n: f"{plural(n, 'place')} for marionberry pie, Oregon's official state pie, each checked in {CHECKED} against a 2026 source, by town."],
               lambda n: f"{plural(n, 'place')} for marionberry pie, Oregon's official state pie, each checked in {CHECKED} against a 2026 source.",
               """<h2>The state pie</h2>
    <p>The legislature named marionberry pie Oregon's official state pie in 2017. The marionberry is a blackberry developed in Oregon and named for Marion County.</p>""",
               "Oregon marionberry pie", "place"),
}
for k, _ in GUIDE_TAGS:
    h1, titles, descs, lede, about, list_name, noun = GUIDE_DEFS[k]
    n = len(L[k])
    guide(k, h1, [t(n) for t in titles], [d(n) for d in descs], lede(n), about, list_name, noun)

# ---------------------------------------------------------------- MICHELIN & James Beard
guide_page(HON_PATH, "Oregon James Beard restaurants", f"{BRAND} · honors current as of {CHECKED}",
           [f"Oregon James Beard Restaurants & Chefs | {BRAND}", "James Beard Restaurants in Oregon, 2025 to 2026",
            f"James Beard Award Restaurants in Oregon | {BRAND}"],
           [f"{plural(len(HON_L), 'Oregon restaurant')} honored by the James Beard Foundation: 2025 and 2026 winners, finalists and semifinalists, and America's Classics, by town.",
            f"{plural(len(HON_L), 'Oregon restaurant')} named by the James Beard Foundation in 2025 or 2026, or as an America's Classic, from Portland to Ashland, by town."],
           f"{plural(len(HON_L), 'Oregon restaurant')} and bar named by the James Beard Foundation: winners, finalists and semifinalists from 2025 and 2026, and America's Classics ({plural(N_CLASSICS, 'place')}). Oregon has no MICHELIN Guide.",
           f"""<h2>What counts as an honor here</h2>
    <p>One source, reported as facts rather than scores: the James Beard Foundation's Restaurant and Chef Awards for 2025 and 2026 (semifinalists, finalists and winners, each labeled as exactly that) and its America's Classics awards from any year. Where an honor went to a chef, the line under the place names the chef. Reader polls, "best of" roundups and review-site stars don't count, and there's no MICHELIN Guide for Oregon.</p>
    <p class="fine">James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. {BRAND} is not affiliated with it.</p>""",
           HON_L, "restaurant", "restaurants", "Oregon James Beard restaurants", honors=True)

# ---------------------------------------------------------------- oldest
if HAS_OLD:
    oldest_named = next((p for p in OLD_L if p.promo_ok()), None)
    assert all(p.founded <= 1960 for p in OLD_L), "the oldest-places copy says 'since 1960 or earlier'"
    from_line = f" The oldest, {e(oldest_named.name)} in {e(oldest_named.city)}, goes back to {oldest_named.founded}." if oldest_named else ""
    guide_page(OLD_PATH, "Oregon's oldest restaurants", checked_kicker(),
               [f"Oregon's Oldest Restaurants: {len(OLD_L)} Places, Oldest First", f"Oldest Restaurants in Oregon: {len(OLD_L)} Places | {BRAND}"],
               [f"{plural(len(OLD_L), 'Oregon restaurant')} open at the same address since 1960 or earlier, oldest first, each with a note on what its founding year rests on."],
               f"Restaurants and taverns that have fed Oregon from the same address since 1960 or before: {plural(len(OLD_L), 'place')} in all, oldest first.{from_line}",
               """<h2>Which year counts</h2>
    <p>We count from the year a place opened at its current address in its current form, going by the place's own history or a published one.</p>""",
               OLD_L, "place", "places", "Oregon's oldest restaurants", region=False, show_fn=True)

# ---------------------------------------------------------------- the inspections explainer (no results: Oregon publishes none in bulk)
OAR_157 = "https://secure.sos.state.or.us/oard/displayDivisionRules.action?selectedDivision=1328"
url = f"{DOMAIN}/{INS_PATH}"
nav, bc = crumbs([("Home", "/"), ("Oregon restaurant inspections", "/" + INS_PATH)])
title = fit([f"Oregon Restaurant Inspections, Explained | {BRAND}", "Oregon Restaurant Inspection Scores, Explained"], 50, 60, "inspections title")
desc = fit(["How Oregon scores restaurant inspections out of 100, what the Complied and Failed to Comply notices at the door mean, and why this app shows no results.",
            "Oregon restaurant inspections: the score out of 100, the notice posted at the entrance, where results are published, and why this guide doesn't show any."],
           140, 160, "inspections description")
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · state rules</p>
    <h1>Oregon restaurant inspections, explained</h1>
    <p class="lede">Oregon's county health departments inspect licensed restaurants and score each full inspection out of 100. The results go on a statewide portal you can search one place at a time, but no one publishes them in bulk, so {BRAND} shows none and computes no grade of its own. Here is how the score works, and what to look for at the door.</p>
  </section>
  <section id="groups">
    <h2>The score and the notice</h2>
    <p class="sub">Under Oregon's rules (<a href="{OAR_157}" rel="noopener">OAR 333-157</a>), an inspection starts at 100. Each Priority violation, the kind that can directly cause foodborne illness, costs 5 points; each Priority Foundation violation, which supports a Priority item, costs 3; a repeat doubles either. Core items count separately.</p>
    <ul class="groups"><li><h3>What's posted at the entrance</h3><ul><li><span class="res res-ok">Complied</span> a score of 70 or more: the notice says the restaurant "complied with the acceptable sanitation standards"</li><li><span class="res res-low">Failed to comply</span> a score under 70; two in a row within 30 days close the restaurant until it passes again</li></ul></li></ul>
    <p>Food carts (mobile units) and commissaries are inspected but not scored, so a cart has no score to post. One inspection is a snapshot of one day.</p>
  </section>
  <section id="lookup">
    <h2>Where the results are</h2>
    <p>Oregon's 33 local health jurisdictions, covering all 36 counties, record their inspections on one shared portal run with the Oregon Health Authority. It lets you look up one place at a time and doesn't allow apps or automated reading, and we found no bulk copy, so the results aren't here. What {BRAND} does show for each place: its active liquor license from the Oregon Liquor and Cannabis Commission, where it holds one. Look a place up in the <a href="/explore/">{BRAND} web app</a>.</p>
    <p class="fine">{other_guides("/" + INS_PATH)}</p>
  </section>
  </main>"""
page(INS_PATH, title, desc, body, [article_ld(url, "Oregon restaurant inspections, explained", desc), bc])

# ---------------------------------------------------------------- city pages
city_stats = {}
SEC_DEFS = [  # key, long title phrase, short title phrase, h1 phrase, description phrase builder (guides with a page only)
    d for d in [
    ("cart", "Food Carts", "Food Carts", "food carts", lambda n: plural(n, "hand-checked food cart")),
    ("brewpub", "Brewpubs", "Brewpubs", "brewpubs", lambda n: plural(n, "licensed brewpub")),
    ("seafood", "Coast Seafood", "Seafood", "coast seafood", lambda n: plural(n, "chowder, crab or oyster spot")),
    ("donut", "Doughnut Shops", "Doughnuts", "doughnut shops", lambda n: plural(n, "doughnut shop")),
    ("wine", "Wine Country Dining", "Wine Country", "wine country dining", lambda n: plural(n, "wine country restaurant")),
    ("taqueria", "Taquerías", "Taquerías", "taquerías", lambda n: plural(n, "taquería")),
    ("marion", "Marionberry Pie", "Marionberry Pie", "marionberry pie", lambda n: plural(n, "place", "places") + " for marionberry pie"),
    ] if d[0] in L]
SEC_ORDER = [k for k, *_ in SEC_DEFS] + ["hon", "oldest"]
CITY_INFO = {}
for c in CITY_PAGES:
    here = [p for p in REST if p.city == c]
    info = {k: sorted([p for p in L[k] if p.city == c], key=P.featured_key) for k, _ in GUIDE_TAGS}
    info["hon"] = sorted([p for p in HON_L if p.city == c], key=P.featured_key)
    info["oldest"] = [p for p in OLD_L if p.city == c] if HAS_OLD else []
    info["cuis"] = Counter(p.cuisine for p in here if p.cuisine and p.cuisine not in ("Other", "American & Other")).most_common(10)
    info["n_town"] = len(here)
    listed, seen = [], set()
    for k in SEC_ORDER:
        for p in info[k]:
            if id(p) not in seen:
                seen.add(id(p)); listed.append(p)
    info["listed"] = listed
    CITY_INFO[c] = info
    city_stats[c] = {"restaurants": len(here), "listed": len(listed), **{k: len(info[k]) for k in SEC_ORDER}}


def city_sections(info):
    """The sections a city page has, biggest first: (key, long, short, h1 phrase, description phrase)."""
    out = [(k, lt, st, h1p, dp(len(info[k]))) for k, lt, st, h1p, dp in SEC_DEFS if info[k]]
    if info["hon"]:
        out.append(("hon", "James Beard", "James Beard", "James Beard honorees", plural(len(info["hon"]), "James Beard honoree")))
    if info["oldest"]:
        k_old = len(info["oldest"])   # "1 of Oregon's oldest restaurants", not "the oldest restaurants" (one place isn't the town's all)
        out.append(("oldest", "Oldest Restaurants", "Oldest Places", "oldest restaurants",
                    f"1 of Oregon's oldest restaurants (from {info['oldest'][0].founded})" if k_old == 1
                    else f"{k_old} of Oregon's oldest restaurants (back to {info['oldest'][0].founded})"))
    return sorted(out, key=lambda s: (-len(info[s[0]]), SEC_ORDER.index(s[0])))


def tjoin(xs):
    if len(xs) == 1:
        return xs[0]
    conj = " and " if any("&" in x for x in xs) else " & "
    return ", ".join(xs[:-1]) + conj + xs[-1]


def city_title(c, secs):
    cands = []
    for k in range(min(len(secs), 3), 0, -1):
        for col in (1, 2):
            J = tjoin([s[col] for s in secs[:k]])
            # "<town> restaurants" is what people search, so those forms come first
            forms = ([f"{c} Restaurants: {J}", f"{c}, OR Restaurants: {J}", f"{c} Restaurants: {J} | {BRAND}", f"{c}, Oregon Restaurants: {J}"]
                     if "Restaurant" not in J else [])
            forms += [f"{c} {J} | {BRAND}", f"{c}, OR {J} | {BRAND}", f"{c}, Oregon {J}", f"{c}, OR {J}", f"{c} {J}"]
            if "Restaurant" not in J:
                forms += [f"{c} {J} & Restaurants", f"{c} {J} & Restaurants | {BRAND}", f"{c}, Oregon {J} & Restaurants"]
            cands += forms
    cands += [f"{c} Restaurants: What {c} Eats | {BRAND}", f"{c}, Oregon Restaurants by Kind | {BRAND}", f"{c}, OR Restaurants, Cafés & Bars | {BRAND}",
              f"{c}, Oregon Restaurants, Cafés and Bars", f"{c} Restaurants, Cafés & Bars | {BRAND}", f"{c}, Oregon: Restaurants, Carts & More | {BRAND}",
              f"{c}, OR: Food Carts & Restaurants | {BRAND}"]
    return fit(cands, 50, 60, c + " title")


def city_desc(c, info, secs):
    n_town = info["n_town"]
    leads = [f"In {c}, Oregon", f"{c}, Oregon", f"{c}, OR"]
    tails = [f". Search {n_town:,} {c} restaurants, cafés and bars", f". Search {n_town:,} local places to eat",
             f", plus {n_town:,} local places to eat on a searchable map", f", plus {n_town:,} more local places to eat", ""]
    extras = ["", f" Checked in {CHECKED}.", " Free iPhone app coming soon.", f" Checked in {CHECKED}. Free iPhone app coming soon."]

    def gen():
        for k in range(len(secs), 0, -1):
            J = join_words([s[4] for s in secs[:k]])
            for lead in leads:
                for tail in tails:
                    for x in extras:
                        yield f"{lead}: {J}{tail}.{x}"
    return fit(list(dict.fromkeys(s.replace("..", ".") for s in gen())), 140, 160, c + " description")


SEC_HEAD = {"cart": ("Food carts", "cart"), "brewpub": ("Brewpubs", "brewpub"), "seafood": ("Coast seafood", "seafood"),
            "donut": ("Doughnut shops", "donut"), "wine": ("Wine country dining", "wine"), "taqueria": ("Taquerías", "taqueria"),
            "marion": ("Marionberry pie", "marion")}
GUIDE_COUNT_NOUN = {"cart": "Oregon food carts and pods", "brewpub": "Oregon brewpubs", "seafood": "Oregon coast seafood places",
                    "donut": "Oregon doughnut shops", "wine": "wine country restaurants", "taqueria": "Oregon taquerías",
                    "marion": "places for marionberry pie"}
SINGULAR = {"Oregon food carts and pods": "Oregon food cart or pod", "Oregon brewpubs": "Oregon brewpub",
            "Oregon coast seafood places": "Oregon coast seafood place", "Oregon doughnut shops": "Oregon doughnut shop",
            "wine country restaurants": "wine country restaurant", "Oregon taquerías": "Oregon taquería",
            "places for marionberry pie": "place for marionberry pie"}

for c in CITY_PAGES:
    info = CITY_INFO[c]
    path = f"cities/{slug(c)}.html"
    url = DOMAIN + "/" + path
    anchors = Anchors(url)
    secs = city_sections(info)
    title = city_title(c, secs)
    desc = city_desc(c, info, secs)
    k = 3
    while k > 1 and len(join_words([s[3] for s in secs[:k]])) > 48:   # a heading, not the whole table of contents
        k -= 1
    h1_bits = [s[3] for s in secs[:k]]
    h1 = f"{c} restaurants" + (": " + join_words(h1_bits + (["more"] if len(secs) > k else [])) if secs else "")
    nav, bc = crumbs([("Home", "/"), ("Cities", "/cities/"), (c, "/" + path)])
    counts = [s[4] for s in secs]
    n_hc = sum(1 for p in info["listed"] if p.hc and p.tags & HC_TAGS)
    lede = (f"What {e(c)} has on our lists: {e(join_words(counts))}. "
            + (f"Each hand-checked place had a source when we looked in {CHECKED}. " if n_hc else "")
            + f"In all, {BRAND} maps {info['n_town']:,} restaurants, cafés, bars and bakeries in {e(c)}, nearest first on your phone.")
    parts = [f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · {e(c)}, Oregon</p>
    <h1>{e(h1)}</h1>
    <p class="lede">{lede}</p>
    <div class="cta-row">{store_button()}<span class="pill store-note">{STORE_NOTE}</span></div>
  </section>"""]
    for s in secs:
        key = s[0]
        if key in SEC_HEAD:
            head, gk = SEC_HEAD[key]
            how = (f"Each holds an active OLCC Brewery Public House license (read {e(hdate(LIC_UPDATED))})." if key == "brewpub"
                   else f"Each one checked in {CHECKED}.")
            parts.append(f'<section id="{key}" aria-labelledby="h-{key}"><h2 id="h-{key}">{e(head)} in {e(c)}</h2><p class="sub">{how} For all of Oregon: <a href="/{GUIDE_PATH[gk]}">{plural(len(L[gk]), SINGULAR.get(GUIDE_COUNT_NOUN[gk], GUIDE_COUNT_NOUN[gk][:-1]), GUIDE_COUNT_NOUN[gk])}</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors) for p in info[key]) + "</ol></section>")
        elif key == "hon":
            parts.append(f'<section id="honors" aria-labelledby="h-honors"><h2 id="h-honors">James Beard honorees in {e(c)}</h2><p class="sub">Restaurants named by the James Beard Foundation, reported as facts rather than scores. Across Oregon: <a href="/{HON_PATH}">{plural(len(HON_L), "Oregon James Beard restaurant")}</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors, honors=True) for p in info["hon"]) + "</ol></section>")
        elif key == "oldest":
            parts.append(f'<section id="oldest" aria-labelledby="h-oldest"><h2 id="h-oldest">Oldest restaurants in {e(c)}</h2><p class="sub">In business at this address since 1960 or before, going by the place itself or a published history, listed from the oldest. Each note gives the source of the year. Across Oregon: <a href="/{OLD_PATH}">Oregon\'s oldest restaurants</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors, show_fn=True) for p in info["oldest"]) + "</ol></section>")
    if info["cuis"]:
        rows = "".join(f'<tr><td>{e(k)}</td><td class="n">{n:,}</td></tr>' for k, n in info["cuis"])
        parts.append(f'<section id="cuisines" aria-labelledby="h-cuisines"><h2 id="h-cuisines">What {e(c)} eats</h2><p class="sub">Kinds of food among the {info["n_town"]:,} places we list in {e(c)}, counted from open map data and the state\'s liquor license list.</p><table><thead><tr><th scope="col">Kind of place</th><th scope="col" class="n">Places</th></tr></thead><tbody>{rows}</tbody></table></section>')
    parts.append(f'<section id="more" aria-labelledby="h-more"><h2 id="h-more">Other Oregon towns with a page</h2>{city_links(current=c)}<p class="fine"><a href="/cities/">The cities and towns index</a></p></section>\n  </main>')
    lds = [article_ld(url, h1, desc), bc]
    if info["listed"]:
        lds.append(item_list(f"{c}: " + join_words([s[3] for s in secs]), info["listed"], url, anchors))
    page(path, title, desc, "\n".join(parts), lds)


# ---------------------------------------------------------------- cities index
url = f"{DOMAIN}/cities/"
nav, bc = crumbs([("Home", "/"), ("Cities", "/cities/")])
cards = []
for c in CITY_PAGES:
    info = CITY_INFO[c]
    bits = [f"{s[3]} ({len(info[s[0]])})" for s in city_sections(info)]
    line = (join_words(bits) + ". " if bits else "") + f"{info['n_town']:,} places to eat in all."
    cards.append(f'<a class="card" href="{city_url(c)}"><h3>{e(c)}</h3><p>{e(line[0].upper() + line[1:])}</p></a>')
first, last = CITY_PAGES[:2], CITY_PAGES[-2:]
title = fit([f"Oregon Cities & Towns: Restaurant Guides | {BRAND}", f"Oregon City Restaurant Guides: {plural(len(CITY_PAGES), 'Town')} | {BRAND}",
             f"Oregon Towns: Food Carts, Brewpubs & Restaurant Guides"], 50, 60, "cities title")
desc = fit([f"Restaurant guides for {plural(len(CITY_PAGES), 'Oregon city and town', 'Oregon cities and towns')}: food carts, brewpubs, coast seafood, doughnut shops and James Beard honors.",
            f"City-by-city Oregon restaurant guides for {plural(len(CITY_PAGES), 'town')}: food carts and pods, brewpubs, chowder and crab, doughnuts and James Beard honors."],
           140, 160, "cities description")
skipped_line = (f" Other towns get a page once they have at least {MIN_LISTED} hand-checked or honored places; until then, "
                f'<a href="/explore/">search them</a>.')
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · cities and towns</p>
    <h1>Oregon cities and towns</h1>
    <p class="lede">A page for Oregon cities and towns that have enough hand-checked, licensed or honored places to say something real: the food carts, brewpubs, coast seafood, doughnut shops and James Beard honorees that are actually there.{skipped_line}</p>
  </section>
  <section id="cities-list">
    <h2>Pick a town</h2>
    <div class="grid2">{"".join(cards)}</div>
  </section>
  </main>"""
page("cities/index.html", title, desc, body, [bc], og_type="website")

# ---------------------------------------------------------------- web app (docs/explore/): data split + page
# The web app lists restaurants only (the venues the app hides by default, such as stadium stands and gas-station counters, stay out).
# Three kinds of file, to keep the first load small for ~25,000 places:
# - core.json: the list, search and map columns. Places are ordered by region, county, town, zip and street, so neighbouring rows
#   share their town, zip and street words and gzip well; coordinates are integer steps of 0.0001° from the previous row ("dla"/"dlo"),
#   and the latest inspection is [city, result, priority count] plus a day number from 2000-01-01 ("idn").
# - ids.json: each place's stable id (the app's id), in core order. Fetched right after the list renders; saved places and shared
#   #p= links wait for it.
# - detail-<county>.json: phones, websites, notes, licenses and inspection histories, keyed by core index, one file per county
#   (Wayne's is the biggest), fetched when someone opens (or points at) a place there.
os.makedirs(f"{DOCS}/data", exist_ok=True)
DFILES = [slug(c) for c in COUNTIES] + ["other"]   # detail file per county index; "other" for a place with no county
CAL = {a: {"groups": {g: {"n": v.get("n"), "official": v.get("official")} for g, v in (c.get("groups") or {}).items()}}
       for a, c in (D.get("calibration") or {}).items() if isinstance(c, dict)}
DAY0 = "2000-01-01"


def day_num(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return (dt.date(int(m[1]), int(m[2]), int(m[3])) - dt.date(2000, 1, 1)).days if m else None


def street_key(a):
    m = re.match(r"\s*(\d+)\s*(.*)", a or "")
    return (m[2].lower(), int(m[1]) if len(m[1]) < 9 else 0) if m else ((a or "").lower(), 0)


def web_order(p):
    rg = REGION_ORDER.index(p.region) if p.region else len(REGION_ORDER)
    return (rg, p.county or "", p.city or "", p.zip, street_key(p.addr), p.name.lower(), p.r["id"])


WEB = sorted(REST, key=web_order)
CORE_KEYS = ["n", "c", "co", "cu", "t", "s", "a", "z", "b", "ch", "g", "hc", "ip", "f", "h", "dish", "liq"]
cols = {k: [] for k in CORE_KEYS + ["dla", "dlo", "jb", "ij", "ib", "isc", "idn"]}
ids, shards = [], defaultdict(dict)
prev = [0, 0]
for i, p in enumerate(WEB):
    r = p.r
    ids.append(r["id"])
    for k in CORE_KEYS:
        v = r.get(k)
        if k == "a" and v:
            v = p.addr
        cols[k].append(v)
    for k, j, v in (("dla", 0, p.lat), ("dlo", 1, p.lon)):
        if v is None:
            cols[k].append(None)
        else:
            q = round(v * 10000)
            cols[k].append(q - prev[j])
            prev[j] = q
    dk = r["co"] if r.get("co") is not None else len(COUNTIES)   # the detail file this place's extras go in
    if r.get("co") is None:
        cols["co"][-1] = len(COUNTIES)
    cols["jb"].append(1 if r.get("jbf") else None)
    for k in ("ij", "ib", "isc", "idn"):   # inspection columns the shared web app reads: always empty in Oregon
        cols[k].append(None)
    d = {k: r[k] for k in ("ph", "note", "seas", "fn", "jbf", "lic") if r.get(k)}
    if p.site:
        d["w"] = p.site
    if d:
        shards[dk][str(i)] = d
assert len(set(ids)) == len(ids), "place ids must be unique (saved places and #p= links use them)"
for f in glob.glob(f"{DOCS}/data/detail*.json"):   # files from an older layout or a region that emptied
    os.remove(f)
# columns that are mostly empty (hand-checked and honored facts) go as [[index, value], ...] instead of 25,000 nulls
sparse = {k: [[i, v] for i, v in enumerate(cols.pop(k)) if v is not None]
          for k in list(cols) if sum(v is not None for v in cols[k]) < len(WEB) * 0.05}
core = {"generated": D["generated"], "inspections_through": {}, "liquor_updated": LIQ_UPDATED, "licenses_updated": LIC_UPDATED,
        "guides": [k for k, _ in ALL_GUIDES if L_ALL[k]], "day0": DAY0, "n": len(WEB), "cities": CITIES, "cuisines": CUISINES, "counties": COUNTIES + ["Oregon"],
        "brands": D["brands"], "srcs": D["srcs"], "results": [], "itypes": [], "calibration": CAL, "cols": cols, "sparse": sparse,
        "dfiles": [f if dk in shards else None for dk, f in enumerate(DFILES)]}   # null: that county has no extras, so no file
assert all("," not in x for x in ids)
# ids and details are keyed by row, so a file from one build must never meet another build's core.json (a browser cache can outlive a
# deploy by GitHub's 10 minutes): every file carries the build's version, the page fetches with ?v=, and the web app refuses a mismatch
DATA_VER = hashlib.sha256(json.dumps([core, ids, shards], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
DETAIL_FILES = {}
for dk, d in sorted(shards.items()):
    fn = f"detail-{DFILES[dk]}.json"
    json.dump({"_v": DATA_VER, **d}, open(f"{DOCS}/data/{fn}", "w"), separators=(",", ":"), ensure_ascii=False)
    DETAIL_FILES[fn] = len(d)
json.dump({"ver": DATA_VER, **core}, open(f"{DOCS}/data/core.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump({"v": DATA_VER, "ids": ",".join(ids)}, open(f"{DOCS}/data/ids.json", "w"), separators=(",", ":"))   # one string: smaller than an array
json.dump(json.load(open(f"{ROOT}/data/or/or_shapes.json")), open(f"{DOCS}/data/or_shapes.json", "w"), separators=(",", ":"))


def sizes(path):
    raw = open(path, "rb").read()
    return len(raw), len(gzip.compress(raw, 9))


SIZES = {os.path.relpath(f, DOCS): sizes(f) for f in sorted(glob.glob(f"{DOCS}/data/*.json"))}

EXPLORE_CSS = """
  [hidden] { display: none !important; }
  .ex-hero { padding: 28px 0 8px; }
  .ex-hero h1 { font-size: clamp(30px, 9.38vw, 42px); }
  .ex-controls { background: var(--bg); padding: 10px 0 8px; border-bottom: 1px solid var(--rule); }
  .ex-guides { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: none; }
  @media (min-width: 601px) { .ex-guides { flex-wrap: wrap; overflow: visible; } }
  @media (max-width: 600px) { .ex-guides { padding-right: 32px; -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 32px), transparent); mask-image: linear-gradient(to right, #000 calc(100% - 32px), transparent); } }
  .ex-guides button, .ex-view button, .ex-small { flex: 0 0 auto; border: 1px solid var(--rule); background: var(--surface); color: var(--accent); border-radius: 999px; padding: 7px 12px; font: 600 14px/1.2 system-ui, sans-serif; font-family: inherit; cursor: pointer; }
  .ex-guides button[aria-pressed="true"], .ex-view button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
  .ex-row1 { display: flex; gap: 8px; align-items: center; }
  .ex-row1 input[type=search] { flex: 1; min-width: 0; font: 16px/1.3 system-ui, sans-serif; font-family: inherit; padding: 10px 12px; border: 2px solid var(--accent); border-radius: 12px; background: var(--surface); color: var(--ink); }
  .ex-row2 { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; font-size: 14px; }
  .ex-row2 select { font: 14px system-ui, sans-serif; font-family: inherit; padding: 6px 8px; border: 1px solid var(--rule); border-radius: 8px; background: var(--surface); color: var(--ink); max-width: 46vw; }
  .ex-view { margin-left: auto; display: flex; gap: 4px; }
  #ex-count { margin: 8px 0 0; font-size: 14px; color: var(--muted); }
  #ex-sub { margin: 4px 0 0; font-size: 14px; color: var(--ink2); }
  #ex-locmsg { font-size: 13px; color: var(--muted); margin: 4px 0 0; }
  .ex-list { list-style: none; padding: 0; margin: 10px 0; }
  .ex-list li + li { border-top: 1px solid var(--rule); }
  .ex-row { width: 100%; display: flex; gap: 12px; align-items: center; text-align: left; background: none; border: 0; padding: 12px 4px; cursor: pointer; color: var(--ink); font: inherit; }
  .ex-row:hover { background: var(--surface2); }
  .ex-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; overflow-wrap: anywhere; }
  .ex-main b { font-weight: 650; }
  .ex-town { font-size: 14px; color: var(--muted); }
  .tag-dash { background: transparent; color: var(--muted); border: 1px dashed var(--rule); }
  .ex-metric { text-align: right; display: flex; flex-direction: column; align-items: flex-end; max-width: 46%; }
  .ex-metric b { font: 800 22px/1 var(--display); color: var(--accent); }
  .ex-metric small { font-size: 11px; color: var(--muted); }
  .ex-rank { flex: 0 0 34px; height: 34px; display: grid; place-items: center; font: 800 20px var(--display); color: var(--accent); border-radius: 8px; }
  .ex-rank.top { background: var(--orange); color: var(--on-orange); }
  .ex-empty { padding: 24px 4px; color: var(--muted); }
  #ex-more { display: block; margin: 8px auto 24px; }
  #ex-mapwrap { position: relative; height: min(72vh, 720px); margin: 10px 0 20px; border: 1px solid var(--rule); border-radius: 16px; overflow: hidden; background: #d9e7f1; }
  #ex-map { width: 100%; height: 100%; display: block; touch-action: none; cursor: grab; }
  .ex-zoom { position: absolute; right: 10px; top: 10px; display: flex; flex-direction: column; gap: 6px; }
  .ex-zoom button { width: 44px; height: 44px; border-radius: 10px; border: 1px solid #dde3e3; background: #fff; color: #14305c; font: 700 22px/1 system-ui, sans-serif; cursor: pointer; }
  #ex-maphint { position: absolute; left: 10px; top: 10px; margin: 0; font-size: 13px; background: #fff; padding: 3px 8px; border-radius: 999px; color: #24384a; pointer-events: none; }
  #ex-mapattr { position: absolute; right: 0; bottom: 0; margin: 0; font-size: 11px; background: rgba(255,255,255,.85); padding: 2px 6px; border-radius: 6px 0 0 0; color: #24384a; pointer-events: none; }
  .ex-panel { position: fixed; z-index: 20; right: 0; top: 0; bottom: 0; width: min(440px, 100%); overflow-y: auto; background: var(--surface); border-left: 1px solid var(--rule); box-shadow: -8px 0 24px rgba(0,0,0,.12); padding: 18px 20px 40px; }
  @media (max-width: 600px) { .ex-panel { top: auto; height: 86vh; border-left: 0; border-top: 4px solid var(--orange); border-radius: 18px 18px 0 0; } }
  .ex-close { position: sticky; top: 0; float: right; width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--rule); background: var(--surface); font-size: 24px; line-height: 1; cursor: pointer; color: var(--ink); }
  .ex-kicker { margin: 0; font-size: 12px; font-weight: 700; letter-spacing: .1em; color: var(--accent2); }
  .ex-panel h2 { font-size: 32px; margin: 4px 0 6px; overflow-wrap: anywhere; }
  .ex-addr, .ex-dist { margin: 0 0 4px; color: var(--ink2); font-size: 15px; }
  .ex-actions { margin: 14px 0 8px; display: grid; gap: 8px; }
  .ex-apple { justify-content: center; }
  .ex-act-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .ex-act-row a, .ex-act-row button { flex: 1; min-width: 88px; text-align: center; padding: 10px; border: 1px solid var(--rule); border-radius: 12px; text-decoration: none; color: var(--accent); font: 600 14px system-ui, sans-serif; font-family: inherit; background: var(--surface); cursor: pointer; }
  .ex-act-row button[aria-pressed="true"] { background: var(--soft); color: #0c1d2a; }
  .ex-sec { margin-top: 18px; }
  .ex-sec h3 { font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--rule); padding-bottom: 6px; margin-bottom: 8px; }
  .ex-sec p, .ex-sec li { font-size: 15px; color: var(--ink2); margin: 6px 0; }
  .ex-sec ul { padding-left: 18px; }
  .ex-kv { display: flex; justify-content: space-between; gap: 12px; font-size: 15px; padding: 3px 0; }
  .ex-kv span { color: var(--ink2); flex: 0 0 auto; max-width: 40%; }
  .ex-kv b { text-align: right; overflow-wrap: anywhere; }
  .ex-fine { font-size: 13px !important; color: var(--muted) !important; }
  .ex-result { display: flex; align-items: center; gap: 10px; font-weight: 600; flex-wrap: wrap; }
  .ex-app { margin-top: 22px; font-size: 14px; color: var(--muted); }
  body.ex-open { overflow: hidden; }
  .ex-backdrop { position: fixed; inset: 0; z-index: 19; background: rgba(12, 29, 42, .32); }
  /* phones: 16px or more in the search box and the selects, or iOS Safari zooms the page when one gets focus */
  @media (max-width: 600px) { .ex-row1 input[type=search], .ex-row2 select { font-size: 16px; } }
  /* the sort's longest choice ("Not in compliance first") at 16px: wider than 46vw, so on phones it may use the row */
  @media (max-width: 600px) { #ex-sort { max-width: calc(100vw - 100px); } }
  .ex-res { display: inline-block; font: 800 12px/1.4 -apple-system, system-ui, sans-serif; letter-spacing: .04em; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; text-align: center; }
  .ex-res-ok { background: #ddefe3; color: #0e5a2b; } .ex-res-mid { background: #ffe9c2; color: #6b3a00; } .ex-res-low { background: #f9d5db; color: #7a0019; } .ex-res-x { background: var(--surface2); color: var(--ink2); }
"""
url = f"{DOMAIN}/explore/"
N_HC_GUIDES = len(HC_ANY)
title = fit(["Oregon Restaurant Search: Map, Food Carts & Brewpubs", "Search Oregon Restaurants: Food Carts, Brewpubs & Seafood"], 50, 60, "explore title")
desc = fit([f"Look up {N_REST:,} Oregon restaurants by name, town, street, zip or dish, map {N_HC_GUIDES} hand-checked places and see each one's state liquor license.",
            f"Search {N_REST:,} Oregon restaurants by name, town, street or dish, map {N_HC_GUIDES} hand-checked places, licensed brewpubs and James Beard honorees.",
            f"Search {N_REST:,} Oregon restaurants by name, town or dish, browse {N_HC_GUIDES} hand-checked places on a map and see licensed brewpubs."],
           140, 160, "explore description")
nav, bc = crumbs([("Home", "/"), ("Search", "/explore/")])
WEB_GUIDES = [(k, t) for k, t in (("cart", "Food carts"), ("brewpub", "Brewpubs"), ("seafood", "Coast seafood"), ("marion", "Marionberry pie"),
                                   ("wine", "Wine country"), ("donut", "Doughnut shops"), ("taqueria", "Taquerías")) if L_ALL[k]]
guide_buttons = "".join(f'<button type="button" data-g="{k}" aria-pressed="false">{e(t)}</button>' for k, t in
                        WEB_GUIDES + [("honors", "James Beard"), ("oldest", "Oldest"),
                                      ("all", "All restaurants"), ("saved", "Saved")])
explore_js = open(f"{ROOT}/scripts/explore.js").read()
JS_KEYS = sorted(set(re.findall(r'store\.set\("([a-z]+)"', explore_js)))   # the keys the web app writes, each under STORAGE_PREFIX
assert JS_KEYS and "localStorage.setItem(PREFIX + k" in explore_js and len(re.findall(r"localStorage\.setItem", explore_js)) == 1
assert "</script" not in explore_js.lower()
assert f'"{STORAGE_PREFIX}"' in explore_js, "explore.js must keep its localStorage keys under " + STORAGE_PREFIX
body = f"""{nav}
  <main id="main">
  <section class="ex-hero">
    <p class="kicker">{BRAND} · on the web</p>
    <h1>Search Oregon restaurants</h1>
    <p class="sub">Pick a list, or type a name, a town, a street or a dish. Behind the search: {N_REST:,} Oregon restaurants, cafés, bars and bakeries; {N_HC_GUIDES} hand-checked places on the food cart, coast seafood, doughnut, wine country and taquería lists; {len(L_ALL["brewpub"])} brewpubs with a state Brewery Public House license; {len(HON_L)} James Beard honorees; and each place's Oregon liquor license. It's the data the iPhone and iPad app will ship with, and what you save stays in this browser.</p>
  </section>
  <p id="ex-loading" hidden>Loading the restaurant list…</p>
  <noscript><p>The search needs JavaScript. The guides work without it: <a href="/{GUIDE_PATH['cart']}">food carts</a>, <a href="/{GUIDE_PATH['brewpub']}">brewpubs</a>, <a href="/{GUIDE_PATH['seafood']}">coast seafood</a>, <a href="/{INS_PATH}">inspections explained</a>.</p></noscript>
  <div id="ex-app" hidden data-ver="{DATA_VER}">
    <div class="ex-controls">
      <div class="ex-guides" role="group" aria-label="Guides">{guide_buttons}</div>
      <div class="ex-row1">
        <label class="skip" for="ex-q">Search</label>
        <input id="ex-q" type="search" placeholder="Name, town, street or dish" autocomplete="off" enterkeyhint="search">
        <button type="button" id="ex-locate" class="ex-small">Near me</button>
      </div>
      <div class="ex-row2">
        <label>Sort <select id="ex-sort" aria-label="Sort"></select></label>
        <select id="ex-town" aria-label="Town"></select>
        <select id="ex-cuisine" aria-label="Kind of place"></select>
        <label><input type="checkbox" id="ex-chains"> Hide chains</label>
        <button type="button" id="ex-clear" class="ex-small" hidden>Clear filters</button>
        <div class="ex-view" role="group" aria-label="View"><button type="button" data-v="list" aria-pressed="true">List</button><button type="button" data-v="map" aria-pressed="false">Map</button></div>
      </div>
      <p id="ex-sub"></p>
      <p id="ex-count" aria-live="polite"></p>
      <p id="ex-locmsg"></p>
    </div>
    <div id="ex-listwrap"><ol id="ex-list" class="ex-list"></ol><button type="button" id="ex-more" class="ex-small" hidden></button></div>
    <div id="ex-mapwrap" hidden>
      <canvas id="ex-map" aria-label="Map of Oregon with a dot for each place in the list. The list view has the same places."></canvas>
      <div class="ex-zoom"><button type="button" id="ex-zin" aria-label="Zoom in">+</button><button type="button" id="ex-zout" aria-label="Zoom out">−</button></div>
      <p id="ex-maphint"></p>
      <p id="ex-mapattr">Outlines © OpenStreetMap contributors, Overture Maps Foundation</p>
    </div>
  </div>
  <div id="ex-backdrop" class="ex-backdrop" hidden></div>
  <aside id="ex-panel" class="ex-panel" hidden aria-labelledby="ex-pname"></aside>
  </main>
<script>
{explore_js}
</script>"""
webapp_ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": f"{BRAND} web app", "url": url,
             "applicationCategory": "TravelApplication", "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
             "description": desc, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
             "publisher": ORG_REF}
page("explore/index.html", title, desc, body, [webapp_ld, bc], extra_css=EXPLORE_CSS, og_type="website")

# ---------------------------------------------------------------- landing page
# alt text says what each capture shows (docs/screenshots, made by scripts/capture-screenshots.sh; copies by scripts/site-images.sh)
shots = [("home", "The Oregon Eats home screen: a search box and guide cards for Food Carts & Pods, Brewpubs, Coast Seafood and Doughnut Shops, each with its count of places.", "A guide for each Oregon craving."),
         ("carts", "The hand-checked food cart list in Oregon Eats, nearest first, with each cart's town, kind and distance.", "Food carts nearest you."),
         ("detail", "Nick's Italian Cafe in Oregon Eats: its address, an America's Classic tag, a button for Apple Maps' ratings, hours and photos, Directions and Call buttons, a small map, its James Beard honor and its Oregon liquor license.", "Each place, with its state license."),
         ("map", "The Oregon Eats map around downtown Portland, with pins for hand-checked places and filter buttons for food carts, brewpubs and honors.", "The map, by guide."),
         ("honors", "The James Beard honors list in Oregon Eats.", "James Beard honorees.")]
shot_html = []
for i, (name, alt, cap) in enumerate(shots):
    png = f"{DOCS}/img/screen-{name}.png"
    if not os.path.exists(png):
        continue
    w, h = png_size(png)
    lazy = ' loading="lazy"'   # the section sits below the fold at every width
    webp = os.path.exists(f"{DOCS}/img/screen-{name}.webp")
    src = (f'<source srcset="/img/screen-{name}.webp" type="image/webp">' if webp else "")
    shot_html.append(f'<li><picture>{src}<img src="/img/screen-{name}.png" alt="{e(alt)}" width="{w}" height="{h}"{lazy} decoding="async"></picture><p>{e(cap)}</p></li>')

CART_L, PUB_L, SEA_L = L["cart"], L["brewpub"], L["seafood"]
faq = [
    ("Is Oregon Eats free?", "Completely: no price, no ads, no in-app purchases and no account to create. It's an iPhone and iPad app on its way to the App Store, with no Android version yet; until it's out, the web search here works in any browser."),
    ("Where do the lists come from?", f"Two kinds of source. The food cart, coast seafood, doughnut, wine country and taquería lists are our own research from {CHECKED}: a dated 2025 or 2026 page names each place (local news, an official tourism listing or the place's own site), or an older one does and the place holds an active Oregon liquor license in 2026. The brewpub list and the wider directory of {N_REST:,} restaurants come from the Oregon Liquor and Cannabis Commission's license list and Overture Maps' open place data, keeping the kinds of listing that proved reliable against that license list."),
    ("Where are Portland's food cart pods?", f"Our food cart list has {plural(len(CART_L), 'hand-checked cart or pod', 'hand-checked carts and pods')} in Portland, Bend, Eugene and Springfield, each confirmed at its pod in 2026. In the web search, the Food carts list puts the nearest first once you share your location. Carts move often, so check before you go."),
    ("How do I check an Oregon restaurant's inspection?", "Oregon's county health departments inspect restaurants and score each inspection out of 100, and the notice at the entrance says whether the place complied. The results are on a statewide portal you can search one place at a time; no one publishes them in bulk, so this app doesn't show them."),
    ("Does it show ratings and reviews?", "Not from us. Tapping a place opens Apple Maps' own card inside the app, with Apple's current ratings, hours, photos and directions. None of our lists is sorted by anyone's rating."),
    ("Does it need my location?", "No. Location only matters for putting the nearest places first. If you share it, it stays on your iPhone or iPad and never reaches us, and the app works fine without it. On this website, Near me reads your location inside your browser and nowhere else."),
    ("A place has closed, or something's wrong. How do I tell you?", f"Write to {EMAIL} with the place's name, its town and what changed. Corrections ship with the next data update."),
]
faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": f"{DOMAIN}/#faq",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
app_ld = {"@context": "https://schema.org", "@graph": [
    # No "offers" until the app is on the App Store (put it back with the listing URL: price 0, USD).
    {"@type": "MobileApplication", "@id": f"{DOMAIN}/#app", "name": APP_NAME,
     "alternateName": ["Oregon Eats", "Oregon Eats: Food Carts, Brewpubs & Chowder"],
     "description": f"A free guide to {N_REST:,} Oregon restaurants, checked against the state's liquor license list, with hand-checked lists of food carts and pods, coast seafood, doughnut shops, wine country dining and taquerías, {len(PUB_L)} licensed brewpubs and {len(HON_L)} James Beard honorees. Sort by distance, open Apple Maps' live place card for hours and photos, and save places for your next trip.",
     "url": f"{DOMAIN}/", "image": f"{DOMAIN}/og.png", "operatingSystem": "iOS, iPadOS", "applicationCategory": "TravelApplication",
     "applicationSubCategory": "Food & Drink", "inLanguage": "en", "publisher": {"@id": ORG_ID}},
    {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": f"{DOMAIN}/",
     "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png", "width": 512, "height": 512}, "email": EMAIL,
     "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": EMAIL, "availableLanguage": "en"},
     # the Eats Ranked hub lists this site as a subOrganization; say so from this side too
     "parentOrganization": HUB},
    {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "name": BRAND, "alternateName": ["Oregon Eats app"], "url": f"{DOMAIN}/",
     "inLanguage": "en", "publisher": {"@id": ORG_ID}}]}
if shot_html:
    app_ld["@graph"][0]["screenshot"] = f"{DOMAIN}/img/screen-{next(n for n, *_ in shots if os.path.exists(f'{DOCS}/img/screen-{n}.png'))}.png"
title = fit(["Oregon Eats: Food Carts, Brewpubs & Oregon Restaurant App", "Oregon Eats: Food Carts, Chowder & Restaurant App"], 50, 60, "landing title")
desc = fit([f"Food carts, brewpubs and coast chowder: a free iPhone and iPad guide to {N_REST:,} Oregon restaurants, with hand-checked lists and state licenses.",
            f"A free iPhone and iPad guide to {N_REST:,} Oregon restaurants, with hand-checked food carts, coast seafood and doughnut shops, plus licensed brewpubs.",
            f"Free iPhone and iPad guide to {N_REST:,} Oregon restaurants: hand-checked food carts, chowder and crab, doughnuts, plus brewpubs and James Beard honorees."],
           140, 160, "landing description")
city_cards = "".join(f'<li><a href="{city_url(c)}">{e(c)}</a></li>' for c in CITY_PAGES)
screens = f"""
  <section id="screens">
    <h2>Inside the app</h2>
    <ul class="shots" tabindex="0" aria-label="Oregon Eats app screenshots">
      {"".join(shot_html)}
    </ul>
  </section>""" if shot_html else ""
CARD_LINE = {"cart": " confirmed at their pods", "seafood": ", chowder to oysters", "donut": ", Burns to Beaverton", "wine": " among the vineyards",
             "taqueria": " and taco carts", "marion": " for the state pie"}
guide_cards = "".join(
    f'<a class="card gc gc-{k}" href="/{GUIDE_PATH[k]}"><b>{len(L[k])}</b><h3>{e(GUIDE_NAME[k])}</h3><p>'
    + (f'{plural(len(L[k]), "place")} with a state Brewery Public House license' if k == "brewpub" else f'{plural(len(L[k]), "hand-checked place")}{CARD_LINE.get(k, "")}')
    + '.</p></a>' for k, _ in GUIDE_TAGS)
body = f"""  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND}: {TAGLINE} for iPhone and iPad</p>
    <h1>Oregon restaurants, carts to chowder</h1>
    <p class="lede">Looking for a food cart pod at lunch, a brewpub after a hike, a bowl of chowder on the coast or a box of doughnuts for the drive? {BRAND} starts with lists we checked place by place, adds the brewpubs that hold a state Brewery Public House license and James Beard honorees, and maps {N_REST:,} restaurants, cafés, bars and bakeries in {N_TOWNS:,} Oregon towns, {N_OFFICIAL:,} of them holding an Oregon liquor license.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/">Search on the web</a><span class="pill store-note">No charge, no ads, no sign-in. The App Store release is on its way.</span></div>
    <ul class="stats" aria-label="What's in the app">
      <li><b>{N_HC_GUIDES}</b><span>hand-checked places</span></li>
      <li><b>{len(PUB_L)}</b><span>licensed brewpubs</span></li>
      <li><b>{len(HON_L)}</b><span>James Beard honorees</span></li>
      <li><b>{N_REST:,}</b><span>restaurants</span></li>
    </ul>
  </section>

  <section id="what">
    <h2>Built around how Oregon eats</h2>
    <p class="sub">Star ratings won't tell you which pod a cart moved to, or which coast town still makes its chowder from scratch. {BRAND} is organized the way people here eat: food carts, brewpubs, coast seafood, doughnut shops, wine country and taquerías, each hand-checked place backed by a source from {CHECKED}. Every place shows its Oregon liquor license where it has one, and Apple Maps' live card supplies ratings, hours and photos.</p>
  </section>

  <section id="how">
    <h2>How it works</h2>
    <ol class="steps">
      <li class="step"><div class="n" aria-hidden="true">1</div><div><h3>Start with a craving.</h3><p>Food Carts &amp; Pods, Brewpubs, Coast Seafood, Doughnut Shops, Wine Country, Taquerías or James Beard Honors. Or type a name, a town, a street or a dish to search the {N_REST:,} we list.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">2</div><div><h3>Find the closest one.</h3><p>Put the nearest first, narrow it to one town or one kind of food, or pan the map from Astoria to Ontario.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">3</div><div><h3>Head out.</h3><p>Check today's hours and photos on Apple Maps' card, call ahead, get directions, or save the place for the next road trip.</p></div></li>
    </ol>
  </section>
{screens}
  <section id="guides">
    <h2>Oregon food guides</h2>
    <p class="sub">Each of the app's lists has its own page here, free to read.</p>
    <div class="grid2">
      {guide_cards}
      {f'<a class="card gc gc-oldest" href="/{OLD_PATH}"><b>{len(OLD_L)}</b><h3>Oregon&#39;s oldest restaurants</h3><p>{plural(len(OLD_L), "place")} open at the same address since 1960 or earlier.</p></a>' if HAS_OLD else ""}
      <a class="card gc gc-honors" href="/{HON_PATH}"><b>{len(HON_L)}</b><h3>James Beard honors</h3><p>{plural(len(HON_L), "honored Oregon restaurant")}.</p></a>
      <a class="card" href="/{INS_PATH}"><h3>Oregon inspections, explained</h3><p>How the state scores restaurants out of 100, what the notice at the door means, and why this guide shows no results.</p></a>
    </div>
  </section>

  <section id="cities">
    <h2>Carts, brewpubs and more by city</h2>
    <p class="sub">The towns with enough hand-checked, licensed or honored places for a page of their own. The <a href="/cities/">cities and towns index</a> sums up what's on each.</p>
    <ul class="cities">{city_cards}</ul>
  </section>

  <section id="pricing">
    <h2>Free, with no catch</h2>
    <p class="sub">The app costs nothing, shows no ads and sells nothing inside, and there's no account to make. The lists ship inside the app, so they open right away and keep working when the signal drops out on the coast range.</p>
  </section>

  <section id="privacy">
    <h2>What stays on your phone</h2>
    <p class="sub">{BRAND} collects nothing about you: no sign-in, no analytics, no ads. Location, if you turn it on, only puts the nearest places first, and your saved places are kept on the phone or iPad. The website has no cookies and no trackers. <a href="/privacy.html">The privacy policy</a> has the details.</p>
  </section>

  <section id="faq">
    <h2>Questions</h2>
    {faq_html}
  </section>

  <section id="download" class="final">
    <h2>Find your next food cart</h2>
    <p class="sub">The iPhone and iPad app is almost here, and it's free. Ask for early access.</p>
    <div class="cta-row">{store_button()}</div>
  </section>
  </main>"""
page("index.html", title, desc, body, [app_ld, faq_ld], og_type="website")

# ---------------------------------------------------------------- privacy and terms
nav, bc = crumbs([("Home", "/"), ("Privacy policy", "/privacy.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Privacy policy</h1>
    <p class="lede">Short version: the {BRAND} app collects nothing about you, and this website doesn't track you. Last updated {PRIVACY_UPDATED}.</p>
  </section>
  <section>
    <h2>The app</h2>
    <ul>
      <li><b>No account, no analytics, no ads.</b> The app has no sign-in, no advertising and no analytics or crash-reporting code. We receive no data from it.</li>
      <li><b>Location.</b> If you allow it, your location is used on your device to sort places by distance and show where you are on the map. It is never sent to us. You can turn it off in Settings at any time.</li>
      <li><b>Saved places and filters</b> are stored only on your device and are deleted when you delete the app.</li>
      <li><b>Apple Maps.</b> When you open a place's ratings, hours and photos, or ask for directions, the app asks Apple Maps for that place. Apple handles that request under <a href="https://www.apple.com/legal/privacy/" rel="noopener">Apple's privacy policy</a>, as it does for any app that shows a map.</li>
      <li><b>Data updates.</b> When you open the app, it checks this website for newer restaurant data, at most once a day (or an hour later if a check didn't go through), and downloads it when there is some. These requests carry no location or identifiers. GitHub, which hosts this site, may keep standard server logs of them, as it does for any visit here.</li>
      <li><b>Spotlight.</b> The app adds its hand-checked and honored places to your device's search index so you can find them from Spotlight. That index stays on your device.</li>
      <li><b>Calls, websites and email</b> you start from a place open in the Phone app, your browser or Mail, and are handled by them.</li>
    </ul>
    <p>When the app is on the App Store, its privacy label will be "Data Not Collected".</p>
    <h2>This website</h2>
    <p>The site is static pages hosted on GitHub Pages. It sets no cookies and loads no analytics, fonts or scripts from anyone else.</p>
    <ul>
      <li><b>Saved places and your last guide.</b> The search page (<a href="/explore/">/explore/</a>) keeps the places you save and the last guide you opened in your browser's local storage, on this device only, under the keys {join_words([f"<code>{STORAGE_PREFIX}{k}</code>" for k in JS_KEYS])}. Nothing is sent to us. Clearing this site's data in your browser removes them.</li>
      <li><b>Location.</b> If you tap Near me or choose the Nearest sort, your browser asks whether to share your location. If you allow it, the location is used only inside your browser to sort places by distance and is never sent to us or anyone else.</li>
    </ul>
    <p>GitHub may keep standard server logs, such as IP addresses, for security; see <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub's privacy statement</a>.</p>
    <h2>Email</h2>
    <p>If you email us, we use your message and address only to reply and to fix the listing you told us about. We don't add you to a mailing list or share your address. Mail to {EMAIL} reaches our inbox through Cloudflare Email Routing; see <a href="https://www.cloudflare.com/privacypolicy/" rel="noopener">Cloudflare's privacy policy</a>.</p>
    <h2>Children</h2>
    <p>The app collects no personal information from anyone, including children.</p>
    <h2>Changes and contact</h2>
    <p>If this policy changes, the new version will be posted here with a new date. Questions: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  </section>
  </main>"""
page("privacy.html", "Oregon Eats Privacy Policy: No Tracking, No Accounts",
     fit(["How Oregon Eats treats your data: the iPhone app collects none, your location and saved places stay on your device, and this site uses no cookies or trackers.",
          "How Oregon Eats treats your data: the app collects none, your location and saved places stay on your device, and this site has no cookies or trackers.",
          "How Oregon Eats handles your data: the iPhone app collects none, your location and saved places stay on your device, and this site uses no cookies or trackers."], 140, 160),
     body, [bc])

nav, bc = crumbs([("Home", "/"), ("Terms of use", "/terms.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Terms of use</h1>
    <p class="lede">The plain-language terms for the {BRAND} app and this website. Last updated {POLICY_UPDATED}.</p>
  </section>
  <section>
    <h2>What the app is</h2>
    <p>{BRAND} is a free guide to restaurants in Oregon. It is provided as is, for personal use, without charge and without warranties of any kind.</p>
    <h2>Check before you go</h2>
    <p>Restaurants open, close, change their hours and change their menus, food carts move, and many coast places keep seasonal hours. Dishes and founding years are what each place or a named source said when we checked in {CHECKED}. We work to keep the lists right, but we can't promise that any listing is current or complete. Call the restaurant before you make the trip.</p>
    <h2>Public records</h2>
    <p>Liquor licenses come from the Oregon Liquor and Cannabis Commission's list on the state's open data portal, shown with the license type, number and expiration date OLCC publishes; licensee names are left out. Oregon publishes no restaurant inspection results in bulk, so the app and this site show none and compute no grade. A missing license means unknown, not unlicensed. For official records, ask the agency itself.</p>
    <h2>Other people's content</h2>
    <p>Ratings, reviews, hours and photos in each place card come from Apple Maps and are Apple's and its providers', under Apple's terms. Restaurant names and trademarks belong to their owners. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. {BRAND} is not affiliated with any restaurant, chain, award body or government agency.</p>
    <h2>Data sources and licenses</h2>
    <ul>
      <li>Oregon Liquor and Cannabis Commission, Liquor Business Licenses &amp; Endorsements (data.oregon.gov), modified for use here.</li>
      <li>Overture Maps Foundation places data, under the Community Data License Agreement, Permissive 2.0, including data from Meta, Microsoft, DAC, BrightQuery, AllThePlaces (CC0 1.0) and Foursquare (Apache 2.0).</li>
      <li>Overture Maps Foundation divisions, used for the state and county outlines on the map, under the Open Database License: © OpenStreetMap contributors, Overture Maps Foundation.</li>
      <li>The James Beard Foundation's awards, semifinalists, finalists and America's Classics: honors reported as facts.</li>
      <li>Food carts and pods, coast seafood, marionberry pie, wine country, doughnut shops, taquerías and founding years: our own research, with a source recorded for every place.</li>
    </ul>
    <h2>Corrections</h2>
    <p>If a listing is wrong, or you own a restaurant and want something fixed, email <a href="mailto:{EMAIL}">{EMAIL}</a>. We fix mistakes in the next update.</p>
    <h2>Liability</h2>
    <p>To the extent the law allows, we are not liable for any loss arising from use of the app or site, including a wasted drive to a closed restaurant.</p>
    <h2>Changes</h2>
    <p>We may update these terms; the current version and its date are always on this page. See also the <a href="/privacy.html">privacy policy</a>.</p>
  </section>
  </main>"""
page("terms.html", "Oregon Eats Terms of Use: A Free Guide, Provided As Is",
     fit(["The terms for Oregon Eats and this site: a free restaurant guide provided as is, public records shown as the agencies published them, and how to report a mistake.",
          "The terms for Oregon Eats and this website: a free guide provided as is, public records shown as the agencies published them, and how to report a mistake.",
          "The terms for Oregon Eats and this website: a free restaurant guide provided as is, state records shown as published, and how to report a mistake to us."], 140, 160),
     body, [bc])

body = f"""  <main id="main">
  <section class="hero">
    <h1>Page not found</h1>
    <p class="lede">No page lives at this address. Head back to the <a href="/">{BRAND} home page</a>, the <a href="/{GUIDE_PATH['cart']}">food cart list</a> or the <a href="/explore/">Oregon restaurant search</a>.</p>
  </section>
  </main>"""
page("404.html", f"Not found: {BRAND}", "No page lives at this address.", body, robots="noindex,follow")
noindexed.remove("404.html")


# ---------------------------------------------------------------- plumbing
for f in os.listdir(f"{DOCS}/cities"):   # a city the data lost: drop its old page instead of leaving it live and stale
    if f.endswith(".html") and f"cities/{f}" not in written + noindexed:
        os.remove(f"{DOCS}/cities/{f}")
        print("removed stale", f"cities/{f}")
urls = ["" if w == "index.html" else w.replace("index.html", "") for w in written]
urls.sort(key=lambda u: (u != "", u.startswith("cities/"), u))
open(f"{DOCS}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + "".join(f"  <url><loc>{DOMAIN}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(f"{DOCS}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
json.dump({"name": BRAND, "short_name": "Oregon Eats", "description": f"{TAGLINE[0].upper() + TAGLINE[1:]}: a guide to {N_REST:,} Oregon restaurants.",
           "start_url": f"{BASE}/", "display": "browser", "background_color": "#f7f3ea", "theme_color": "#14305c",
           "icons": [{"src": f"{BASE}/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": f"{BASE}/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(f"{DOCS}/site.webmanifest", "w"), indent=2)
if CUSTOM_DOMAIN:
    open(f"{DOCS}/CNAME", "w").write(CUSTOM_DOMAIN + "\n")
elif os.path.exists(f"{DOCS}/CNAME"):
    os.remove(f"{DOCS}/CNAME")   # no custom domain yet: GitHub serves the project address
open(f"{DOCS}/.nojekyll", "w").write("")
os.makedirs(f"{ROOT}/playbook", exist_ok=True)
json.dump({"generated": TODAY, "domain": DOMAIN, "restaurants": N_REST, "places_incl_hidden": len(PLACES), "towns": N_TOWNS, "counties": N_COUNTIES,
           "on_an_official_list": N_OFFICIAL, "serves_alcohol": N_LIQ, "hand_checked_on_a_guide": N_HC,
           **{"guide_" + k: len(v) for k, v in L_ALL.items()}, "guide_pages": list(L), "oldest": len(OLD_L), "honors": len(HON_L), "james_beard": N_JBF,
           "americas_classics": N_CLASSICS,
           "liquor_updated": LIQ_UPDATED, "licenses_updated": LIC_UPDATED, "olcc_active_onprem": N_OLCC, "olcc_active_full": N_OLCC_FULL,
           "city_pages": city_stats, "cities_without_a_page": CITY_SKIPPED, "noindex_pages": noindexed,
           "web_app_data_bytes": {k: {"raw": r, "gzip": g} for k, (r, g) in SIZES.items()}},
          open(f"{ROOT}/playbook/site-numbers.json", "w"), indent=1, ensure_ascii=False)
print("wrote", len(written) + len(noindexed) + 1, "pages:", ", ".join(written))
if noindexed:
    print("noindex:", ", ".join(noindexed))
print(f"restaurants {N_REST:,} in {N_TOWNS} towns | official {N_OFFICIAL:,} | hand-checked on a guide {N_HC} | "
      + " | ".join(f"{k} {len(v)}" for k, v in L_ALL.items()) + f" | oldest {len(OLD_L)} | honors {len(HON_L)}")
print("city pages:", ", ".join(CITY_PAGES), "| no page (listed places):", CITY_SKIPPED)
print(f"website blocklist: {len(BLOCKLIST)} entries, {len(BLOCKED_LINKS)} links dropped:", "; ".join(f"{n} {u}" for n, u in BLOCKED_LINKS) or "none")
for k, (r, g) in SIZES.items():
    print(f"  {k}: {r / 1024:,.0f} KB raw, {g / 1024:,.0f} KB gzip")
