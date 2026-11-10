"""Step 10: page data. data/site_streets.geojson (every street with a Booth colour: name, colour code, purity; coordinates to
5 decimals), data/site_lsoa.geojson (LSOAs touching the map: code, name, borough, IMD 2025 decile and score, Booth poverty
share, classified street length, analysis flag, group), data/site.json (headline numbers and the search list)."""
import numpy as np
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
cl = S[S.booth != ""]
CI = {c: i for i, c in enumerate(CLASSES)}
feats = []
for r in cl.itertuples():
    xy = [[round(float(a), 5), round(float(b), 5)] for a, b in (p.split() for p in r.coords.split(";"))]
    dd = [xy[0]] + [p for i, p in enumerate(xy[1:], 1) if p != xy[i - 1]]
    feats.append({"type": "Feature", "properties": {"n": r.name, "c": CI[r.booth], "p": round(float(r.purity), 2)},
                  "geometry": {"type": "LineString", "coordinates": dd}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/site_streets.geojson")

O = pd.read_csv(f"{DATA}/lsoa_booth.csv")
A = pd.read_csv(f"{DATA}/lsoa_analysis.csv", keep_default_na=False)
inA = set(A.lsoa21cd)
grp = dict(zip(A.lsoa21cd, A.group))
place = dict(zip(A.lsoa21cd, A.place))
G = jload(f"{DATA}/lsoa_london.geojson")
Oi = O.set_index("lsoa21cd")
for ft in G["features"]:
    c = ft["properties"]["c"]; r = Oi.loc[c]
    ps = r.poor_share if np.isfinite(r.poor_share) else None
    ft["properties"] = {"c": c, "nm": r.lsoa21nm, "b": r.lad24nm, "d": int(r.imd_decile), "s": round(float(r.imd_score), 1),
                        "ps": None if ps is None else round(float(ps) * 100, 1), "km": round(float(r.classified_m) / 1000, 2),
                        "a": 1 if c in inA else 0, "g": grp.get(c, ""), "pl": place.get(c, "")}
jsave(G, f"{DATA}/site_lsoa.geojson")

# search list: named streets (one entry per name and nearest 200 m cluster) and neighbourhoods
srch = []
for (nm, gx, gy), g in cl[cl.name != ""].assign(gx=(cl.lon / 0.006).round(), gy=(cl.lat / 0.004).round()).groupby(["name", "gx", "gy"]):
    m = g.length_m.idxmax()
    srch.append([nm, round(float(g.lon[m]), 5), round(float(g.lat[m]), 5), CI[g.booth[m]]])
places = A[A.place != ""].groupby("place")[["lon", "lat"]].mean()
for nm, r in places.iterrows():
    srch.append([nm, round(float(r.lon), 5), round(float(r.lat), 5), -1])
site = {"n_lsoa": R["n"]["lsoa_analysis"], "rho": R["main_rho"]["rho"], "search": srch}
jsave(site, f"{DATA}/site.json")
for f in ("site_streets.geojson", "site_lsoa.geojson", "site.json"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
