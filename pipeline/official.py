"""Official records for Oregon -> one table of licensed food and drink businesses.

Sources (see playbook/12-sources.md):
- "liq": Oregon Liquor and Cannabis Commission (OLCC), "Liquor Business Licenses & Endorsements" (data.oregon.gov Socrata srxe-qkm2,
         refreshed daily): every liquor license OLCC issued since 2001, with its type, trade name, physical address, county, effective and
         expiration dates, the "license expired" flag, an inactive date and the "Lottery on Premises" flag. No coordinates.
         licensee_name is the license holder (a company or a person): kept only to recognize listings named for the holder, never shown.
Oregon has no statewide food-license or inspection data in bulk (the HealthSpace portal is search-only and its robots.txt disallows
all crawlers), so OLCC is the only official list.

load() returns: jur, lic (our id), name, keys (name keys), addr, city, zip, num, street, lat, lon, kind, active, ltype, holder, county,
lottery, expires.
kind: restaurant | bar | brewery | maker | retail | venue | other.
"""
import os, re, json
import numpy as np, pandas as pd
from common import norm_name, RAW, name_sim, _stems, GENERIC, canon_city

OFF = os.path.join(RAW, "official")
DIRS = {"N": "N", "S": "S", "E": "E", "W": "W", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
TYPES = set("ST STREET AVE AV AVENUE BLVD BOULEVARD RD ROAD DR DRIVE LN LANE CT COURT PL PLACE PKWY PARKWAY TER TRL TRAIL WAY HWY CIR "
            "CIRCLE PLZ SQ MALL BND PASS XING RUN ROW WALK RDG LOOP FWY FREEWAY EXPY EXPRESSWAY".split())


def road(a):
    """One spelling for numbered roads: 'US HIGHWAY 101' = 'US-101' = 'HWY 101' = 'OR-101'; 'OR-99W' = 'HIGHWAY 99W';
    'INTERSTATE 84' = 'I-84' = 'I 84'; 'COUNTY ROAD 12' = 'CR 12'. Oregon's US and state route numbers don't collide, so all are HWY."""
    a = re.sub(r"(\d)\s*&\s*(\d)", r"\1-\2", a.upper())
    a = re.sub(r"\b(US|OR|CR|I|ORE)-(\w)", r"\1 \2", a)
    a = re.sub(r"\b(?:INTERSTATE(?: HIGHWAY| HWY)?|IH|I H)\s*(?=\d)", "I ", a)
    a = re.sub(r"\b(?:US|U S)(?:\s+(?:HIGHWAY|HWY))?\s+(?=\d)", "HWY ", a)
    a = re.sub(r"\b(?:STATE (?:HIGHWAY|HWY|ROUTE|RTE)|OREGON (?:HIGHWAY|HWY|ROUTE)|ORE? (?:HIGHWAY|HWY|ROUTE)|HWY OR|HIGHWAY OR|OR|ORE)\s+(?=\d)", "HWY ", a)
    a = re.sub(r"\b(?:COUNTY (?:HIGHWAY|HWY|ROAD|RD)|CO RD|CTY (?:HWY|RD)|CR)\b", "CR", a)
    a = re.sub(r"\bHIGHWAY\b", "HWY", a)
    # Portland's quadrants are part of the street ("3449 NE 24th" and "3449 SE 24th" are miles apart): one spelling, kept in the key
    a = re.sub(r"\b(NORTH|SOUTH)\s*(EAST|WEST)\b", lambda m: m.group(1)[0] + m.group(2)[0], a)
    a = re.sub(r"\b([NS])\.\s*([EW])\.", r"\1\2", a)
    return re.sub(r"\b(CR|HWY|I) (\w+)\s*-\s*\w+", r"\1 \2", a)


QUADS = {"NE", "NW", "SE", "SW"}
ORD = {"FIRST": "1ST", "SECOND": "2ND", "THIRD": "3RD", "FOURTH": "4TH", "FIFTH": "5TH", "SIXTH": "6TH", "SEVENTH": "7TH",
       "EIGHTH": "8TH", "NINTH": "9TH", "TENTH": "10TH", "ELEVENTH": "11TH", "TWELFTH": "12TH"}


def street_key(a):
    """'2505 Monroe St' -> ('2505', 'MONROE'); '1000 OSAGE STREET' -> ('1000', 'OSAGE'); 'E Jefferson Ave' keeps 'JEFFERSON'."""
    if not isinstance(a, str):
        return None, None
    a = re.sub(r"[.,#]", " ", road(a))
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*\d+[A-Z]?)?\s+(.*)$", a)
    if not m:
        return None, None
    words = [w for w in m.group(2).split() if w]
    if len(words) > 1 and words[0] in DIRS:
        words = words[1:]
    core = []
    for w in words:
        if w in TYPES and core:
            break
        core.append(w)
    core = [ORD.get(w, w) for w in core]
    quad = 1 if core and core[0] in QUADS else 0   # "NE MARTIN LUTHER KING": the quadrant doesn't use up a word
    return m.group(1), " ".join(core[:3 + quad]) or None


def street_compat(a, b):
    """Same street, or one is a whole-word prefix of the other (a record that truncates "1206 CENTAUR" = Centaur Village Dr)."""
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        return False
    return a == b or a.startswith(b + " ") or b.startswith(a + " ")


def street_nums(a):
    """'157-159 W Main St' -> {'157', '159'}; '2505 Monroe St' -> {'2505'}."""
    if not isinstance(a, str):
        return set()
    a = road(a)
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*(\d+)[A-Z]?)?\s", a.upper() + " ")
    if not m:
        return set()
    lo = int(m.group(1)); hi = int(m.group(2)) if m.group(2) else lo
    if hi < lo:   # "1500-02"
        hi = int(str(lo)[: len(str(lo)) - len(m.group(2))] + m.group(2)) if m.group(2) else lo
    return {str(x) for x in range(lo, hi + 1, 2 if (hi - lo) % 2 == 0 else 1)} if 0 <= hi - lo <= 12 else {str(lo)}


def _names(*vals):
    out = []
    for v in vals:
        if not isinstance(v, str):
            continue
        v = re.sub(r"\s*\((?:MOBILE|MOBILE UNIT|COMMISSARY|CATERING|SPECIAL EVENT|SPEC EVENT|TEMP(?:ORARY)? EVENT|CP|INSIDE [^)]*)\)\s*$", "", v, flags=re.I)
        for part in re.split(r"\s*/\s*|\s+\bdba\b\s+|\s+&\s+(?=[A-Z][a-z])|\s*\(\s*|\s*\)\s*", v, flags=re.I):
            k = norm_name(re.sub(r"\b(?:LLC|INC|CORP|CORPORATION|LTD|CO)\b\.?", "", part, flags=re.I))
            if k and k not in out:
                out.append(k)
    return out


# OLCC license types. Full On-Premises Commercial: bars and restaurants that serve spirits (Oregon requires them to offer food). Limited
# On-Premises: beer, wine and cider for on-site drinking (taverns, restaurants, but also theaters, salons and bowling alleys). Brewery
# Public House: a brewpub. Makers' consumption licenses: winery, brewery and distillery tasting rooms. Private clubs and "other public
# locations" (stadiums, theaters, airports) are venues; Off-Premises is a store; the rest are makers, wholesalers, shippers and caterers.
LIQ_KIND = {"FULL ON-PREMISES SALES - COMMERCIAL": "restaurant", "LIMITED ON-PREMISES SALES": "bar",
            "BREWERY PUBLIC HOUSE": "brewery", "BREWERY PUBLIC HOUSE ADDITIONAL LOCATION": "brewery",
            "WINERY - CONSUMPTION": "maker", "WINERY - CONSUMPTION ADDITIONAL LOCATION": "maker", "BREWERY - CONSUMPTION": "maker",
            "BREWERY - CONSUMPTION ADDITIONAL LOCATION": "maker", "DISTILLERY TASTING ADDITIONAL LOCATION": "maker",
            "GROWER SALES PRIVILEGE - CONSUMPTION": "maker", "GROWER SALES PRIVILEGE - CONSUMPTION ADD LOCATION": "maker",
            "FULL ON-PREMISES SALES - NON-PROFIT PRIVATE CLUB": "venue", "FULL ON-PREMISES SALES - FOR-PROFIT PRIVATE CLUB": "venue",
            "FULL ON-PREMISES SALES - OTHER PUBLIC LOCATIONS": "venue", "FULL ON-PREMISES SALES - PUBLIC PASSENGER CARRIER": "other",
            "FULL ON-PREMISES SALES - CATERER": "other", "OFF-PREMISES SALES": "retail"}
# short labels shown with a place
LIQ_LABEL = {"FULL ON-PREMISES SALES - COMMERCIAL": "Full On-Premises (beer, wine, spirits)",
             "LIMITED ON-PREMISES SALES": "Limited On-Premises (beer, wine, cider)", "BREWERY PUBLIC HOUSE": "Brewery Public House",
             "BREWERY PUBLIC HOUSE ADDITIONAL LOCATION": "Brewery Public House", "WINERY - CONSUMPTION": "Winery tasting room",
             "WINERY - CONSUMPTION ADDITIONAL LOCATION": "Winery tasting room", "BREWERY - CONSUMPTION": "Brewery tasting room",
             "BREWERY - CONSUMPTION ADDITIONAL LOCATION": "Brewery tasting room", "DISTILLERY TASTING ADDITIONAL LOCATION": "Distillery tasting room",
             "GROWER SALES PRIVILEGE - CONSUMPTION": "Grower tasting room", "GROWER SALES PRIVILEGE - CONSUMPTION ADD LOCATION": "Grower tasting room",
             "FULL ON-PREMISES SALES - NON-PROFIT PRIVATE CLUB": "Private club", "FULL ON-PREMISES SALES - FOR-PROFIT PRIVATE CLUB": "Private club",
             "FULL ON-PREMISES SALES - OTHER PUBLIC LOCATIONS": "Full On-Premises (public venue)", "OFF-PREMISES SALES": "Off-Premises (store)"}
ONPREM = ("restaurant", "bar", "brewery", "maker")
LIST_DATE = open(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "official", "olcc_licenses.fetched")).read().strip() \
    if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "official", "olcc_licenses.fetched")) else None


def liq_kind(t):
    return LIQ_KIND.get((t or "").strip(), "other")


def _zip(z):
    z = re.sub(r"\D", "", str(z or ""))
    return z[:5] if len(z) >= 5 else ""


OTHER = re.compile(r"\((?:MOBILE|MOBILE UNIT|COMMISSARY|CATERING|SPECIAL EVENT|TEMP(?:ORARY)? EVENT)\)|\b(?:SCHOOLS?|ELEMENTARY|MIDDLE SCHOOL|HIGH SCHOOL|"
                   r"ACADEMY|PRESCHOOL|CHILDCARE|CHILD CARE|DAYCARE|DAY CARE|HOSPITAL|JAIL|DETENTION|CORRECTIONAL|FOOD BANK|SENIOR|NURSING|"
                   r"MOBILE|FOOD TRUCK|CATERING|CATERER|COMMISSARY|CONCESSIONS?|BOOSTERS?|PTA|PTO|BOARD OF EDUCATION|PUBLIC SCHOOLS|"
                   r"LITTLE LEAGUE|ATHLETIC ASSOCIATION|SNACK SHACK|CAMP)\b", re.I)


def _row(jur, lic, name, addr, city, z, la, lo, kind, active=True, ltype=None, holder=None, county=None, lottery=False, expires=None):
    num, st = street_key(addr)
    return {"jur": jur, "lic": lic, "name": name, "dba": name, "holder": holder, "keys": _names(name), "addr": addr, "city": city,
            "zip": _zip(z), "num": num, "street": st, "lat": la, "lon": lo, "kind": kind, "active": active, "ltype": ltype,
            "county": county, "lottery": lottery, "expires": expires}


def split_address(a, city):
    """'1210 SW DORION AVE PENDLETON OR  97801-1941' + 'PENDLETON' -> ('1210 SW DORION AVE', '97801')."""
    a = re.sub(r"\s+", " ", (a or "").strip())
    m = re.match(r"^(.*?)\s+OR\s+(\d{5})(?:-\d{0,4})?$", a)
    street, z = (m.group(1), m.group(2)) if m else (a, "")
    c = re.sub(r"\s+", " ", (city or "").strip().upper())
    if c and street.upper().endswith(" " + c):
        street = street[: -len(c) - 1]
    return street.strip(" ,"), z


def load_olcc():
    rows = []
    for r in json.load(open(f"{OFF}/olcc_licenses.json")):
        cty = (r.get("county") or "").strip()
        if not cty or cty.startswith("**"):   # "**Outside of Oregon": out-of-state shippers and suppliers
            continue
        lt = (r.get("license_type") or "").strip()
        street, z = split_address(r.get("physical_address"), r.get("city"))
        street = re.split(r",|\s+(?:STE|SUITE|UNIT|SPC|SPACE|#)\b", street, flags=re.I)[0].strip()
        name = (r.get("trade_name") or "").strip()
        active = r.get("license_expired") == "No" and not r.get("inactive_date")
        row = _row("liq", "OLCC-" + (r.get("license_number") or "").strip(), name, street, canon_city(r.get("city")), z, np.nan, np.nan,
                   liq_kind(lt), active=active, ltype=lt, holder=(r.get("licensee_name") or "").strip() or None, county=cty + " County",
                   lottery=r.get("lottery_on_premises") == "Yes", expires=r.get("license_expires"))
        row["keys"] = _names(name, row["holder"]) if name else _names(row["holder"])
        row["dba"] = name or None
        rows.append(row)
    return pd.DataFrame(rows)


def load():
    df = load_olcc()
    # one business can hold several licenses (a Limited and a Full one over the years, a brewpub and its tasting room): same address and a
    # name in common
    df["biz"] = np.arange(len(df))
    town = df.city.fillna("").str.upper().str.strip()
    for num, g in df[df.num.notna() & df.street.notna()].groupby("num"):
        idx = list(g.index)
        if len(idx) < 2 or len(idx) > 400:
            continue
        for x in range(len(idx)):
            for y in range(x + 1, len(idx)):
                a, b = idx[x], idx[y]
                if not street_compat(df.at[a, "street"], df.at[b, "street"]):
                    continue
                if not ((df.at[a, "zip"] and df.at[a, "zip"] == df.at[b, "zip"]) or (town[a] and town[a] == town[b])):
                    continue
                ka, kb = [norm_name(df.at[a, "dba"] or "")], [norm_name(df.at[b, "dba"] or "")]
                if not ka[0] or not kb[0]:
                    continue
                if any(name_sim(p, q) >= 85 or ((_stems(p) - GENERIC) & (_stems(q) - GENERIC)) for p in ka for q in kb):
                    old, new = df.at[b, "biz"], df.at[a, "biz"]
                    df.loc[df.biz == old, "biz"] = new
    return df
