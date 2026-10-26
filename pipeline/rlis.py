"""Property values for metro Portland (web leaderboard only): the Metro RLIS tax lot under each place's point.

Source: Oregon Metro, Regional Land Information System, "Taxlots (Public) - Download" (ArcGIS item 9d3c396ffad44649bc7451465aa300f0),
the three counties' assessor values (LANDVAL, BLDGVAL, TOTALVAL), year built and land use, with no owner names. Licensed under the RLIS
Open Database End User License Agreement (attribution required; Nick accepted its terms, 2026-10-24):
"Regional Land Information System data are a product of Metro and made publicly available according to the license agreement found in
https://rlisdiscovery.oregonmetro.gov/pages/open-database-license ."
lookup(lat, lon) -> DataFrame (one row per input point, NaN where the point is in no tax lot or outside Multnomah, Washington and
Clackamas). Points on a street (right of way) fall in no lot, and nothing is guessed for them.
"""
import glob, os
import numpy as np, pandas as pd, duckdb

ROOT = os.path.join(os.path.dirname(__file__), "..")
SHP = (glob.glob(f"{ROOT}/data/raw/official/rlis/taxlots/*.shp") or [None])[0]
FETCHED = open(f"{ROOT}/data/raw/official/rlis/fetched.txt").read().strip() if os.path.exists(f"{ROOT}/data/raw/official/rlis/fetched.txt") else None
ATTRIBUTION = ("Regional Land Information System data are a product of Metro and made publicly available according to the license "
               "agreement found in https://rlisdiscovery.oregonmetro.gov/pages/open-database-license .")
CACHE = f"{ROOT}/data/or/rlis_lots.parquet"


def _lots(con):
    """The tax lots with a value, as WKB in Oregon North state plane feet (EPSG:2913), cached as parquet."""
    if not os.path.exists(CACHE):
        con.execute(f"""COPY (SELECT TLID AS tlid, COUNTY AS county, LANDVAL AS land, BLDGVAL AS bldg, TOTALVAL AS total, BLDGSQFT AS sqft,
                               YEARBUILT AS built, LANDUSE AS landuse, HAS_MANY AS many, ST_AsWKB(geom) AS g
                        FROM ST_Read('{SHP}') WHERE TOTALVAL > 0) TO '{CACHE}' (FORMAT PARQUET)""")
    con.execute(f"CREATE OR REPLACE TABLE lots AS SELECT * EXCLUDE (g), ST_GeomFromWKB(g) AS geom FROM '{CACHE}'")


def lookup(lat, lon):
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET geometry_always_xy = true;")
    _lots(con)
    pts = pd.DataFrame({"i": np.arange(len(lat)), "lat": np.asarray(lat, float), "lon": np.asarray(lon, float)})
    con.register("pts_df", pts)
    con.execute("""CREATE OR REPLACE TABLE pts AS SELECT i, ST_Transform(ST_Point(lon, lat), 'EPSG:4326', 'EPSG:2913') AS geom
                   FROM pts_df WHERE lat BETWEEN 45.0 AND 46.0 AND lon BETWEEN -123.5 AND -121.6""")
    hit = con.execute("""SELECT p.i, l.tlid, l.county, l.land, l.bldg, l.total, l.sqft, l.built, l.landuse, l.many
                         FROM pts p JOIN lots l ON ST_Contains(l.geom, p.geom)""").df()
    hit = hit.sort_values("total", ascending=False).drop_duplicates("i")   # overlapping lots (stacked condos): the larger value
    return pts[["i"]].merge(hit, on="i", how="left").drop(columns="i")


if __name__ == "__main__":
    import time
    t = time.time()
    r = lookup([45.5231, 45.5122, 45.4871], [-122.6765, -122.6587, -122.8037])
    print(r.to_string(), round(time.time() - t), "s")
