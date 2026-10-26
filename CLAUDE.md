# Oregon Eats (or-eats) — notes for Claude Code sessions

Started 2026-10-24 from `../state-prompts/OREGON_PROMPT.md` and `../STATE_EATS_PLAYBOOK.md`. Pipeline and app ported from `../mi-eats/`
(link checker and injection detector from `../co-eats/`); never modify another state's folder.

- Brand (Nick, 2026-10-24, `playbook/05-naming.md`): "Oregon Eats: Restaurants", Home Screen "Oregon Eats", subtitle "Food Carts, Brewpubs &
  Chowder", marionberry pie icon on plum #5A1F46 (`scripts/make-brand.swift`, passes icon-style check), state navy #14305C + gold #F2B705 (fill only).
- Sources and calibration: `playbook/12-sources.md`. OLCC licenses are the only statewide official list; no bulk inspections (OHA records
  request drafted in `playbook/records-requests.md`, Nick sends). Metro RLIS property values: web leaderboard only (`pipeline/rlis.py`).
- Private leaderboard artifact: link in `LOCAL.md` (republish site/index.html + oregon.json, or_detail.json, or_shapes.json).
- Rebuild: `cd pipeline && ../.venv/bin/python listings.py && ../.venv/bin/python geocode_official.py && ../.venv/bin/python calibrate.py &&
  ../.venv/bin/python build_research.py && ../.venv/bin/python oregon.py && OR_APP=1 ../.venv/bin/python oregon.py && cd ..`, then
  `cp data/app/places.json data/app/detail-*.json OregonEats/Resources/`, `.venv/bin/python scripts/make-leaderboard.py`, `.venv/bin/python scripts/make-site.py`.
- App: `xcodegen generate`; build/test with `DEVELOPER_DIR="/Applications/Xcode 1.app/Contents/Developer"`, `-derivedDataPath DerivedData`, own
  simulators "OR Eats 6.9" and "OR Eats iPad 13" (udids in data/sim-iphone.txt, data/sim-ipad.txt; one booted at a time, shut down after use).
- Status 2026-10-24 (afternoon): unit 25/25 and UI 6/6 pass on iPhone; on iPad unit 25/25, UI 5/5 (the launch-time test skips itself
  when the Mac's load is high); full site QA OK; App Store frames in playbook/app-store/{iphone,ipad}; listing copy in playbook/06 and 13.
  Nothing committed or pushed.
- No Google-derived data in the app (QA OR-1, 2026-10-26): calibrate.py keeps Google 2021's open share in the web calibration only;
  oregon.py refuses an app export with a Google-style key (GOOGLE_KEY); OregonEatsTests/GoogleDataTests.swift checks the bundle and
  docs/data/app (it failed on the old bundle, 14 google21_open values). Over-the-air copy: scripts/publish_app_data.py (2026-10-26.1).
- Site QA: `.venv/bin/python scripts/qa-site.py` (ported from mi-eats 2026-10-24: Oregon guides, OLCC brewpub panel, inspections explainer
  with no results; `--static` takes ~3 s since the blocklist scan uses a substring prefilter).
- Screenshots: `bash scripts/capture-screenshots.sh <udid>` (screens home carts seafood donuts detail map honors saved about), then
  `bash scripts/site-images.sh`, `scripts/make-site.py`; App Store frames `scripts/appstore-screenshots.py`; listing copy
  `scripts/make-listing.py` (after make-site.py).
- Closures (build_research.py CLOSED): the script finds them in the last export, which has already dropped them, so it keeps last
  run's match from closed_research.json (fixed 2026-10-24: before, every second rebuild brought 5 closed Bend carts back). A closure
  with no street number removes every non-chain listing of exactly that name in that town (oregon.py; the old Otis Cafe had two).
- Share sends `Links.site + explore/#p=<id>` (SHARE-LINK.md); no Bib Gourmand (no MICHELIN in Oregon).
- Outward actions (repo, Pages, ASC, DNS CNAME oregon, records request) need Nick's explicit yes. Support email nick@eatsranked.com.
