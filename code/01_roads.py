"""Step 1: OpenStreetMap streets inside the Booth map. Parses london_osm_roads.tsv, keeps ways whose midpoint lies on a
Booth tile, and writes data/streets.csv.gz (one row per way: osm_id, name, highway, length_m, mid lon/lat, WKT
coordinates rounded to 6 decimals). Ways with no name are kept (they still sample Booth's colours) but flagged."""
import numpy as np
import pandas as pd
from pyproj import Geod
from common import *

G = Geod(ellps="WGS84")
T = Tiles()
rows = []
with open(os.path.join(BOOTH, "london_osm_roads.tsv"), encoding="utf-8") as f:
    next(f)
    for line in f:
        w, name, hw, wkt = line.rstrip("\n").split("\t")
        osm = int(re.search(r"way/(\d+)", w).group(1))
        name = name.strip('"') if name else ""
        hw = hw.strip('"')
        m = re.search(r"LINESTRING\(([^)]*)\)", wkt)
        if not m:
            continue
        xy = np.array([[float(v) for v in p.split()] for p in m.group(1).split(",")])
        if len(xy) < 2:
            continue
        L = G.line_length(xy[:, 0], xy[:, 1])
        # midpoint along the line
        seg = np.hypot(*np.diff(xy, axis=0).T); c = np.r_[0, np.cumsum(seg)]
        t = c[-1] / 2; i = min(np.searchsorted(c, t, side="right") - 1, len(seg) - 1)
        fr = 0 if seg[i] == 0 else (t - c[i]) / seg[i]
        mid = xy[i] + fr * (xy[i + 1] - xy[i])
        px, py = ll2px(mid[0], mid[1])
        if (int(px // 256), int(py // 256)) not in T.idx:
            continue
        rows.append((osm, name, hw, round(L, 1), round(mid[0], 6), round(mid[1], 6),
                     ";".join(f"{a:.6f} {b:.6f}" for a, b in xy)))
S = pd.DataFrame(rows, columns=["osm_id", "name", "highway", "length_m", "lon", "lat", "coords"])
S = S.drop_duplicates("osm_id").sort_values("osm_id")
S.to_csv(f"{DATA}/streets.csv.gz", index=False)
print(len(S), "ways on the Booth map;", round(S.length_m.sum() / 1000), "km;", (S.name == "").sum(), "unnamed")
