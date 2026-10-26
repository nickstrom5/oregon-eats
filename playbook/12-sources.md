# Oregon sources (checked 2026-10-24)

Every host was robots-checked first (`pipeline/check_sources.py`, RFC 9309 matcher; an empty HTTP 202 counts as a bot check).
Numbers are from `data/or/calibration.json` and the 2026-10-24 build; rebuild to refresh them.

## Official records

| Source | What we use it for | Terms | Cadence | Size (2026-10-24) | Verdict |
|---|---|---|---|---|---|
| OLCC "Liquor Business Licenses & Endorsements", data.oregon.gov Socrata **srxe-qkm2** (`/resource/srxe-qkm2.json`) | Statewide spine: "official" tier, "serves alcohol", the brewpub board (Brewery Public House), the lottery flag, licensed bars/restaurants added when the map lacks them | No license field on the dataset. It's state agency data on the state portal, published under ORS 276A.350–374 ("publishable data" = data an agency may not withhold under public-records law). We show trade name, license type, license number and expiry; **never `licensee_name`** (a person or company). Nick to confirm, like Arizona's Maricopa call | Daily | 22,399 rows; 17,754 in-state; **14,127 active** (`license_expired` = No and no `inactive_date`); 5,173 Full On-Premises Commercial, 2,508 Limited On-Premises, 288 Brewery Public House (incl. additional locations), 803 makers' tasting rooms; 2,092 active with Lottery on Premises | **Used** |
| HealthSpace portal, inspections.myhealthdepartment.com/oregon | Would be inspections (P/Pf sanitation score out of 100, "Complied"/"Failed to Comply" notice) | robots.txt answers our checker with a bot check (the prompt saw `Disallow: /` for all agents on 2026-09-27) | Results post after 14 days | 33 local health jurisdictions, 36 counties | **Not usable**: no scraping, no internal API |
| data.oregon.gov catalog | Any bulk inspection data | — | — | Catalog search "inspection" finds only mycv-acm4 (Deschutes County Inspection History, 2015) | **None current** |
| Multnomah's old API (api.multco.us) | — | — | — | Hostname no longer resolves (dig, 2026-10-24) | **Gone** |
| OHA food-safety program pages (oregon.gov/oha) | Rules for the explainer (OAR 333-150 Food Sanitation Rules, OAR 333-157 scoring and posting) | Public | — | — | Usable for text, no data |
| Oregon Metro RLIS "Taxlots (Public)" (ArcGIS item b3cabe5845ec47eab61c54e0c631313c, services2.arcgis.com/McQ0OlIABe29rJJy) | Building/land value board, Multnomah, Washington and Clackamas only | RLIS Open Database EULA (rlisdiscovery.oregonmetro.gov/pages/open-database-license, read through the ArcGIS item API): copy, publish, distribute, combine allowed with the attribution "Regional Land Information System data are a product of Metro…"; no sublicensing; **you must defend and hold Metro harmless** (indemnity). oregonmetro.gov/rlis-live is robots-disallowed for ClaudeBot | Monthly-ish | not fetched | **Not used yet** (needs Nick's OK on the indemnity) |
| BLS QCEW 2025 annual, area 41000 | Size check: 11,511 private NAICS 722 establishments (9,506 restaurants, 1,065 drinking places) | Public domain | Quarterly | — | data.bls.gov answers our checker with a bot check: numbers are the prompt's (not re-fetched) |
| Overture Maps places **2026-10-21.0** (+ divisions, address points) | Statewide base (23,894 eating/drinking listings incl. 846 food carts `food_truck_stand`), state and county outlines, 1.94M OR address points to place OLCC licenses | CDLA-Permissive-2.0 / Apache-2.0 + Foursquare NOTICE (in-app attribution) | Monthly | — | **Used** (Vancouver WA and Idaho dropped by the state polygon) |
| UCSD Google Local 2021 (`meta-Oregon.json.gz`, mcauleylab.ucsd.edu) | 2021 ratings, reviews, price: **web leaderboard only, never the app** | Research dataset | Frozen Sep 2021 | 17,237 food listings | Used (web) |

OLCC licenses carry no coordinates: 15,919 of 17,754 placed on Overture address points by house number + street + zip/town
(`geocode_official.py`); 1,835 unplaced (they still match listings by street address inside their county). Portland quadrants (NE/SE…)
are kept in the street key: 3449 NE 24th and 3449 SE 24th are miles apart.

## Calibration (OLCC, statewide and Multnomah)

Oregon has no food-license list, so listings are measured against **active on-premises OLCC licenses** (Full, Limited, Brewery
Public House, makers' tasting rooms). Many real restaurants serve no alcohol, so the rates are floors; they rank the listing groups.

| Listing group (app grouping, no Google) | n | matches an on-prem license | Google 2021 also open |
|---|--:|--:|--:|
| Meta, confidence ≥ 0.95 | 8,981 | 46.6% | 72.3% |
| Meta 0.90–0.95 | 3,111 | 23.4% | 42.0% |
| BrightQuery ≥ 0.95 | 1,345 | 22.9% | 30.7% |
| Meta < 0.90 | 2,995 | 11.9% | 5.7% |
| Brand feeds (AllThePlaces) | 499 | 4.6% (chains rarely serve alcohol) | 30.5% |
| Other sources (Foursquare, Microsoft…) | 5,606 | 7.3% | 32.4% |
| Closed per Overture or name | 1,274 | 2.1% | 34.8% |

Web grouping: Meta + open in Google 2021 45.0%; Meta only 23.8%; Foursquare only 7.0%; Microsoft only 10.8%; BrightQuery only 15.6%;
Google 2021 says closed 1.8%. **Coverage:** the open listings hold **77.9%** of the 5,053 businesses with an active Full On-Premises
Commercial license (Multnomah 76.2% of 1,592); the build adds the rest from the license list (1,140 added rows).

Keep rules (same as the family): web = Meta, brand feeds, official or hand-checked, minus Google-2021-closed. App = Meta ≥ 0.95,
Meta 0.90–0.95 with a website, brand feeds, official (OLCC), hand-checked. BrightQuery-only rows stay out unless licensed.
Web build 2026-10-24: **16,340 places, 15,448 restaurants** (6,263 official, 4,422 two-source, 4,763 listing-only) in 341 towns.
BLS's 11,511 establishments vs 15,448: the web build still holds closed places Google 2021 couldn't flag and food carts (not in NAICS 722
as fixed sites); the app rule will be tighter. Compare again after the app export.

## Per-county coverage

Inspections: **every county is search-only** (one shared HealthSpace portal), so no county has inspection boards. OLCC covers every county.

| County | Health jurisdiction (HealthSpace path, from the prompt) | Map listings (cleaned) | OLCC active on-premises | of which Full | Full found among open listings |
|---|---|--:|--:|--:|--:|
| Multnomah County | Multnomah County EH (`/multco-eh`) | 7,020 | 2,213 | 1,592 | 76% |
| Washington County | Washington County (`/or-washington-county`) | 2,573 | 857 | 514 | 74% |
| Lane County | Lane County (`/or-lane-county`) | 1,925 | 615 | 344 | 81% |
| Clackamas County | Clackamas County (`/or-clackamas-county`) | 1,734 | 621 | 393 | 83% |
| Marion County | Marion County (`/or-marion-county`) | 1,599 | 509 | 314 | 83% |
| Deschutes County | Deschutes County (`/or-deschutes-county`) | 1,335 | 484 | 302 | 78% |
| Jackson County | Jackson County (`/or-jackson-county`) | 1,204 | 471 | 230 | 84% |
| Yamhill County | Yamhill County (`/or-yamhill-county`) | 533 | 433 | 108 | 75% |
| Douglas County | Douglas County (`/or-douglas-county`) | 502 | 194 | 93 | 75% |
| Linn County | Linn County (`/or-linn-county`) | 481 | 129 | 86 | 83% |
| Clatsop County | Clatsop County (`/or-clatsop-county`) | 466 | 198 | 127 | 79% |
| Lincoln County | Lincoln County (`/or-lincoln-county`) | 447 | 168 | 105 | 78% |
| Benton County | Benton County (`/or-benton-county`) | 432 | 144 | 85 | 91% |
| Josephine County | Josephine County (`/or-josephine-county`) | 389 | 146 | 80 | 75% |
| Klamath County | Klamath County (`/or-klamath-county`) | 352 | 109 | 63 | 75% |
| Umatilla County | Umatilla/Morrow (`/or-umatilla-morrow-county`) | 342 | 126 | 69 | 78% |
| Coos County | Coos County (`/or-coos-county`) | 334 | 109 | 75 | 77% |
| Polk County | Polk County (`/or-polk-county`) | 320 | 126 | 52 | 86% |
| Tillamook County | Tillamook County (`/or-tillamook-county`) | 232 | 101 | 61 | 72% |
| Hood River County | Hood River County (`/or-hood-river-county`) | 215 | 117 | 53 | 72% |
| Columbia County | Columbia County (`/or-columbia-county`) | 183 | 69 | 42 | 88% |
| Curry County | Curry County (`/or-curry-county`) | 160 | 65 | 42 | 67% |
| Malheur County | Malheur County (`/or-malheur-county`) | 160 | 49 | 35 | 89% |
| Wasco County | North Central Public Health District (`/or-north-central-public-health`) | 153 | 64 | 34 | 74% |
| Union County | Union County (`/or-union-county`) | 120 | 41 | 23 | 87% |
| Jefferson County | Jefferson County (`/or-jefferson-county`) | 119 | 39 | 27 | 41% |
| Crook County | Crook County (`/or-crook-county`) | 100 | 32 | 18 | 78% |
| Baker County | Baker County (`/or-baker-county`) | 90 | 40 | 27 | 85% |
| Morrow County | Umatilla/Morrow (`/or-umatilla-morrow-county`) | 59 | 13 | 9 | 44% |
| Wallowa County | Wallowa County (`/or-wallowa-county`) | 57 | 27 | 16 | 62% |
| Harney County | Harney County (`/or-harney-county`) | 53 | 15 | 6 | 83% |
| Lake County | Lake County (`/or-lake-county`) | 41 | 13 | 9 | 56% |
| Grant County | Grant County (`/or-grant-county`) | 38 | 14 | 10 | 40% |
| Sherman County | North Central Public Health District (`/or-north-central-public-health`) | 19 | 5 | 3 | 100% |
| Wheeler County | Wheeler County (`/or-wheeler-county`) | 14 | 4 | 3 | 67% |
| Gilliam County | North Central Public Health District (`/or-north-central-public-health`) | 10 | 4 | 3 | 67% |

## Honors and lists

- **MICHELIN:** no Oregon guide. guide.michelin.com answers our checker with an AWS WAF challenge (empty 202), so the 404 for
  /us/en/oregon/restaurants is the prompt's (2026-09-27). No Bib Gourmand filter (BIB-GOURMAND-FILTER.md applies only with MICHELIN data).
- **James Beard (jamesbeard.org, robots OK):** the prompt's list (2026 Scotch Lodge, Ryan Roadhouse / Nodoguro; 2025 JinJu Patisserie,
  Timothy Wastell / Antica Terra; 2026 finalist Gado Gado; semifinalists Le Pigeon, Coquine, MÄS, JORY; America's Classics Nick's Italian
  Café, McMinnville, 2014). **To confirm on jamesbeard.org in the research pass.**

## Data rules specific to Oregon

- Brewpubs: one OLCC Brewery Public House license tags one place, chosen by the license's trade name (278 tagged on the web build).
- Video-lottery "delis" and gaming taverns: OLCC's Lottery on Premises flag is on 2,092 active licenses, including Abby's, Elmer's and
  Denny's, so the flag alone hides nothing. Hidden (non-restaurant, not removed): lottery flag + a name that's only a deli, or a gaming
  word (lottery, lotto, jackpot, slots, poker, gaming), or the video-poker deli chains Dotty's (Wikipedia: founded in Oregon in 1991
  as video poker delis) and DeDe's Deli (the state's 2014 list of top video lottery retailers, records.sos.state.or.us). The chain and
  gaming-word rules apply even when no license matched (two Dotty's listings had none). Purple Parrot, Platinum Pub, Doozy's and Lucky
  Lizard carry the lottery flag on every license but had no source calling them parlors, so they stay as bars.
- Adult clubs: Portland has many, under plain names (Mary's Club, Sassy's, Acropolis…). Overture's adult category (107 in the box,
  but it also files adult foster homes, video stores and events: those are filtered out) removes 39 on the web build. A checked,
  sourced address list (`data/research/adult_venues.json`) is still empty: **must be filled before the app** (Colorado's lesson).
- Food carts: Overture's `food_truck_stand` is kept (Nick's prompt: keep carts, expect churn). Carts have no inspection score in Oregon.

## Waiting on Nick

- OK to use OLCC's list in the free app (no license stated on the dataset; we never show the licensee).
- Optional: an ORS 192 public-records request to OHA for a statewide HealthSpace inspection extract (outward-facing: Nick sends it).
- RLIS building values: accept the EULA's indemnity clause, or skip the board (current default: skip).
- App Store name collisions (apps.apple.com and itunes.apple.com disallow Claude) and the USPTO lookup: by hand.
