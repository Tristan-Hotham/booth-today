"""Step 7: the scale (misalignment) test. Every LSOA polygon is shifted by 500 m, 1 km, 2 km and 4 km in eight directions; the
Booth measure is re-read under the shifted polygon, while the outcome stays the LSOA's own IMD 2025 score. LSOAs still on the
map (coverage >= 0.9 and >= 300 m of classified street at the shifted position) are kept. Output: data/shift.json."""
import importlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.formula.api as smf
from common import *

L5 = importlib.import_module("05_lsoa")
d = np.load(f"{SCR}/inks.npz"); M = d["M"]; X0 = int(d["X0"]) * 256; Y0 = int(d["Y0"]) * 256
H, W = M.shape
on = M > 0
O = pd.read_csv(f"{DATA}/lsoa_booth.csv")
code_idx = {c: i for i, c in enumerate(f["properties"]["LSOA21CD"] for f in L5.feats)}
assert list(code_idx) == list(O.lsoa21cd)
area_px = O.area_px.values
P = np.load(f"{SCR}/positions.npz")
px, py = ll2px(P["lon"].astype(float), P["lat"].astype(float))
ix = np.clip(np.round(px).astype(int) - X0, 0, W - 1); iy = np.clip(np.round(py).astype(int) - Y0, 0, H - 1)
mpp = 156543.03392 * np.cos(np.radians(P["lat"].astype(float))) / 2 ** Z
MPP0 = 156543.03392 * np.cos(np.radians(51.51)) / 2 ** Z
DIRS = {"N": (0, -1), "NE": (1, -1), "E": (1, 0), "SE": (1, 1), "S": (0, 1), "SW": (-1, 1), "W": (-1, 0), "NW": (-1, -1)}
rows = []
for dist in (0, 500, 1000, 2000, 4000):
    for dn, (ux, uy) in (DIRS.items() if dist else [("none", (0, 0))]):
        n = np.hypot(ux, uy) or 1
        dx, dy = ux / n * dist / MPP0, uy / n * dist / MPP0
        LR = L5.lsoa_raster(dx, dy)
        n_onmap = np.bincount(LR[(LR >= 0) & on], minlength=len(O))
        cov = np.minimum(n_onmap / np.maximum(area_px, 1), 1)
        pl = LR[iy, ix]
        G = L5.lsoa_measures(pl, P, mpp)
        S = L5.summarise(G, len(O))
        D = O[["lsoa21cd", "lad24cd", "msoa", "imd_score"]].copy()
        D["cov"] = cov; D["cm"] = S["classified_m"]; D["poor"] = S["poor_share"]; D["score"] = S["mean_score"]
        D = D[(D["cov"] >= 0.9) & (D.cm >= 300)].dropna(subset=["poor"])
        D["poor10"] = D.poor * 10
        m = smf.ols("imd_score ~ poor10 + C(lad24cd)", data=D).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.msoa)[0]})
        rows.append({"dist": dist, "dir": dn, "n": int(len(D)), "rho": round(float(spearmanr(D.poor, D.imd_score).statistic), 3),
                     "rho_score": round(float(spearmanr(D.score, D.imd_score).statistic), 3),
                     "b": round(float(m.params["poor10"]), 3), "lo": round(float(m.conf_int().loc["poor10"][0]), 3),
                     "hi": round(float(m.conf_int().loc["poor10"][1]), 3)})
        print(rows[-1], flush=True)
T = pd.DataFrame(rows)
summ = {str(k): {"rho_mean": round(float(g.rho.mean()), 3), "rho_min": round(float(g.rho.min()), 3), "rho_max": round(float(g.rho.max()), 3),
                 "rho_score_mean": round(float(g.rho_score.mean()), 3), "b_mean": round(float(g.b.mean()), 3),
                 "b_min": round(float(g.b.min()), 3), "b_max": round(float(g.b.max()), 3), "n_mean": int(g.n.mean())}
        for k, g in T.groupby("dist")}
jsave({"rows": rows, "by_dist": summ}, f"{DATA}/shift.json", indent=1)
print(json.dumps(summ, indent=1))
