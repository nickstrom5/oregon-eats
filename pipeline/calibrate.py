"""How often is a map listing a real, licensed food business? Measured against official lists -> data/or/calibration*.json

Adapted from mi-eats/pipeline/calibrate.py. Oregon has no statewide food-license list (the 33 local health jurisdictions license
restaurants on HealthSpace, which is search-only), so the one official statewide list is OLCC's: active on-premises liquor licenses
(Full On-Premises Commercial, Limited On-Premises, Brewery Public House) and makers' tasting rooms.
- Match rate: the share of each listing group that matches an active on-premises OLCC license. Many real restaurants serve no alcohol
  (cafés, taquerías, food carts, chains like Subway), so this is a floor, not a "real" rate: it ranks the groups against each other.
- Coverage: the share of active Full On-Premises Commercial businesses (bars and restaurants that must serve food) found among the
  open listings. That one is a direct test of how complete the listings are.
- Google 2021 open: the share of each group also listed as open by Google in Sep 2021 (UCSD snapshot), Idaho's second signal.
A match is the same business name nearby, or the same street address with a distinctive name word in common.
"""
import json
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep
from common import OR
from listings_util import official_match

o = pd.read_pickle(f"{OR}/stage1.pkl")
F = pd.read_pickle(f"{OR}/official.pkl")
from shapely import STRtree
_CN = json.load(open(f"{OR}/or_counties_detail.geojson"))
_NAMES = list(_CN)
_GEOMS = [shape(_CN[n]).buffer(0.0003) for n in _NAMES]
_TREE = STRtree(_GEOMS)


def county_of(la, lo):
    if la != la:
        return None
    p = Point(lo, la)
    for i in _TREE.query(p):
        if _GEOMS[i].contains(p):
            return _NAMES[i]
    return None


o["county"] = [county_of(la, lo) for la, lo in zip(o.lat, o.lon)]
# OLCC rows carry their county; a point outside every county outline (a coastal point a little offshore) keeps the record's own
F["county"] = [county_of(la, lo) or (c if isinstance(c, str) and c else None)
               for la, lo, c in zip(F.lat, F.lon, F.get("county", pd.Series([None] * len(F))))]
o.to_pickle(f"{OR}/stage1.pkl")
F.to_pickle(f"{OR}/official.pkl")
base = ~o.j_junk & ~o.j_outside
print("listings with a county:", int(o.county.notna().sum()), "of", len(o))


def groups(L, app=False):
    s = L.src.fillna("none")
    if app:
        conf = L.confidence.fillna(0)
        return np.select([L.ov_closed | L.j_closedname, (s == "meta") & (conf >= 0.95), (s == "meta") & (conf >= 0.9),
                          s.isin(["AllThePlaces", "DAC"]), (s == "BrightQuery") & (conf >= 0.95), s == "meta"],
                         ["closed per Overture/name", "meta_high", "meta_mid", "brand_feed", "bq_high", "meta_low"], "other_sources")
    return np.select([L.closed21, L.ov_closed, (s == "meta") & L.in21, s == "meta", s.isin(["AllThePlaces", "DAC"]) & L.in21,
                      s.isin(["AllThePlaces", "DAC"]), L.in21, s == "Foursquare", s == "BrightQuery", s == "Microsoft"],
                     ["Google 2021 says closed", "Overture says closed", "Meta + open in Google 2021", "Meta only",
                      "brand feed + Google 2021", "brand feed only", "Foursquare/BrightQuery/Microsoft + Google 2021",
                      "Foursquare only", "BrightQuery only", "Microsoft only"], "other")


ONPREM = F.active & F.kind.isin(["restaurant", "bar", "brewery", "maker"])
AREAS = {"Oregon (statewide)": (None, ONPREM, "liq"),
         "Multnomah County (Portland)": ("Multnomah County", ONPREM, "liq")}
res, app = {}, {}
PER = None
for label, (cty, sel, own) in AREAS.items():
    L = o[base & (o.county.notna() if cty is None else o.county == cty)].reset_index(drop=True)
    R = F[sel & (F.county.notna() if cty is None else F.county == cty)].reset_index(drop=True)
    m = {}
    for c_, gl in L.groupby("county").groups.items():   # county by county: "100 Main St" exists in dozens of towns
        gr = R.index[R.county == c_]
        if not len(gr):
            continue
        for i_, j_ in official_match(L.loc[gl].reset_index(drop=True), R.loc[gr].reset_index(drop=True)).items():
            m[gl[i_]] = gr[j_]
    L["hit"] = L.index.map(lambda i: i in m)
    L["hit_full"] = L.index.map(lambda i: i in m and R.kind.iat[m[i]] == "restaurant")
    L["g_open"] = L.in21 & ~L.closed21
    for mode, store in ((False, res), (True, app)):
        L["grp"] = groups(L, mode)
        t = L.groupby("grp").agg(n=("id", "size"), olcc=("hit", "mean"), full=("hit_full", "mean"), g_open=("g_open", "mean")).sort_values("n", ascending=False)
        print(f"\n== {label} ({'app grouping' if mode else 'web grouping'}): {len(L)} listings, {len(R)} active on-premises licenses")
        print(t.assign(olcc=(t.olcc * 100).round(1), full=(t.full * 100).round(1), g_open=(t.g_open * 100).round(1)).to_string())
        # the app ships no Google-derived number (playbook; QA OR-1, 2026-10-26), so only the web grouping keeps Google 2021's open share
        store[label] = {"listings": int(len(L)), "official_records": int(len(R)),
                        "groups": {g: {"n": int(r.n), "official": round(float(r.olcc), 3), "full": round(float(r.full), 3)}
                                      | ({} if mode else {"google21_open": round(float(r.g_open), 3)}) for g, r in t.iterrows()}}
    # the other direction: how many licensed bars and restaurants do the (cleaned, open) map listings hold?
    keepish = ~(L.ov_closed | L.j_closedname | L.closed21)
    got = set(R.biz.iloc[[m[i] for i in L.index[keepish] if i in m]])
    Rr = R[R.kind.eq("restaurant")].drop_duplicates("biz")
    cover = float(np.mean([b in got for b in Rr.biz])) if len(Rr) else None
    print(f"{label}: Full On-Premises Commercial businesses found among open map listings: {cover*100:.1f}% of {len(Rr)}")
    res[label]["coverage"] = round(cover, 3)
    res[label]["official_food"] = int(len(Rr))
    if cty is None:
        per = L.groupby("county").agg(listings=("id", "size"), olcc_match=("hit", "mean"))
        per["olcc_full"] = Rr.groupby("county").size().reindex(per.index).fillna(0).astype(int)
        per["olcc_onprem"] = R.drop_duplicates("biz").groupby("county").size().reindex(per.index).fillna(0).astype(int)
        per["full_found"] = [float(np.mean([b in got for b in Rr[Rr.county == c].biz])) if (Rr.county == c).any() else None for c in per.index]
        print("\n== per county\n" + per.sort_values("listings", ascending=False).round(3).to_string())
        PER = per

json.dump({"areas": res, "per_county": {c: {k: (round(float(v), 3) if isinstance(v, float) else int(v)) for k, v in r.items() if v == v}
                                          for c, r in PER.iterrows()},
           "unplaced_official_records": int(F.lat.isna().sum()), "olcc_fetched": __import__("official").LIST_DATE},
          open(f"{OR}/calibration.json", "w"), indent=1)
json.dump(app, open(f"{OR}/calibration_app.json", "w"), indent=1)
