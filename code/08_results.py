"""Step 8: data/results.json, holding every number quoted anywhere (page, paper, blog, collage, post, README), and the
neighbourhood name of each analysis LSOA (the nearest Wikidata 'area of London', suburb, neighbourhood or locality point
within 1.5 km of its representative point; CC0) in data/lsoa_analysis.csv."""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
from common import *

SETT = os.environ.get("BT_SETT", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
Mo = jload(f"{DATA}/models.json")
Sh = jload(f"{DATA}/shift.json")
Vt = jload(f"{DATA}/validation_test.json")
Vd = jload(f"{DATA}/validation_dev.json")
S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
A = pd.read_csv(f"{DATA}/lsoa_analysis.csv")

# neighbourhood names
T = pd.read_csv(SETT, sep="\t", quoting=3)
T.columns = ["p", "name", "coord", "pop", "type"]
T["type"] = T["type"].str.extract(r'"(.*)"@')[0]
T["name"] = T["name"].str.extract(r'"(.*)"@')[0]
T = T[T.type.isin(["area of London", "suburb", "neighborhood", "locality"])].dropna(subset=["name"])
xy = T.coord.str.extract(r"POINT\(([-\d.]+) ([-\d.]+)\)").astype(float)
T["lon"], T["lat"] = xy[0], xy[1]
T = T[(T.lon > -0.6) & (T.lon < 0.35) & (T.lat > 51.28) & (T.lat < 51.7)].drop_duplicates("name")
tr = Transformer.from_crs(4326, 27700, always_xy=True)
TE, TN = tr.transform(T.lon.values, T.lat.values)
dist, idx = cKDTree(np.c_[TE, TN]).query(A[["E", "N"]].values)
A["place"] = np.where(dist <= 1500, T.name.values[idx], "")
A.to_csv(f"{DATA}/lsoa_analysis.csv", index=False)

cl = S[S.booth != ""]
L = cl.length_m.sum()
share = {c: round(float(cl.length_m[cl.booth == c].sum() / L * 100), 1) for c in CLASSES}
R = {"streets": {"ways_on_map": int(len(S)), "km_on_map": int(round(S.length_m.sum() / 1000)),
                 "ways_classified": int(len(cl)), "km_classified": int(round(L / 1000)),
                 "share": share, "poor_pc": round(sum(share[c] for c in POOR), 1),
                 "poor_purple_pc": round(sum(share[c] for c in POOR_P), 1)},
     "validation": {"test": {k: Vt[k] for k in ("n", "unclear", "n_scored", "n_mixed", "exact", "exact_pc", "within1", "within1_pc", "poor", "poor_single", "purple_pink")},
                    "dev_exact_pc": Vd["exact_pc"]},
     "n": Mo["n"], "main_rho": Mo["main_rho"], "main_fe": Mo["main_fe"], "main_fe_z": Mo["main_fe_z"], "moran": Mo["moran"],
     "spatial_error": Mo["spatial_error"], "loo": {k: Mo["loo"][k] for k in ("rho_min", "rho_max", "b_min", "b_max")},
     "loo_n": len(Mo["loo"]["rows"]),
     "crosstab": Mo["crosstab"], "quintile_cut": Mo["quintile_cut"], "quintile_mean_imd": Mo["quintile_mean_imd"],
     "quintile_share_d12": Mo["quintile_share_d12"], "bq_n": Mo["bq_n"], "top20_n": Mo["top20_n"], "top20_min": Mo["top20_min"], "groups": Mo["groups"], "imd_d12_share_all": Mo["imd_d12_share_all"],
     "poor_share_mean": Mo["poor_share_mean"], "lsoa_no_poor": Mo["lsoa_no_poor"],
     "exploratory": Mo["exploratory"], "shift": Sh["by_dist"]}
R["robust"] = [{"label": r["label"], "planned": r["planned"], "n": r["fe"]["n"], "rho": r["rho"]["rho"], "rho_lo": r["rho"]["lo"],
                "rho_hi": r["rho"]["hi"], "b": r["fe"]["b"], "lo": r["fe"]["lo"], "hi": r["fe"]["hi"], "y": r["y"], "x": r["x"]} for r in Mo["robust"]]
pl = [r for r in R["robust"] if r["planned"] and r["x"] in ("poor_share", "poor_purple_share", "area_poor_share", "hp_poor_share") and r["y"] in ("imd_score",)]
R["robust_range"] = {"rho_min": min(r["rho"] for r in pl), "rho_max": max(r["rho"] for r in pl),
                     "n_ci_above0": sum(r["rho_lo"] > 0 for r in pl), "n": len(pl)}
south = [r for r in R["robust"] if r["label"].startswith("R8b")][0]
north = [r for r in R["robust"] if r["label"].startswith("R8a")][0]
R["thames"] = {"south": south, "north": north}
R["wmode"] = [r for r in R["robust"] if r["label"].startswith("Window")][0]
R["mean_score"] = [r for r in R["robust"] if r["label"].startswith("R2")][0]
R["purple"] = [r for r in R["robust"] if r["label"].startswith("R1")][0]
R["imd_sd"] = round(float(A.imd_score.std()), 2)
R["imd_mean"] = round(float(A.imd_score.mean()), 2)
R["fe_full_range_points"] = round(Mo["main_fe"]["b"] * 10, 1)
R["fe_full_range_sd"] = round(Mo["main_fe"]["b"] * 10 / A.imd_score.std(), 2)
R["shift_drop_1km_pc"] = round((1 - Sh["by_dist"]["1000"]["rho_mean"] / Mo["main_rho"]["rho"]) * 100)
# example neighbourhoods for each group (places with the most LSOAs in the group)
ex = {}
for g in ("persistent", "turned", "fallen"):
    G = A[(A.group == g) & (A.place != "")]
    vc = G.groupby(["place", "lad24nm"]).size().sort_values(ascending=False)
    ex[g] = [{"place": p, "borough": b, "n": int(n)} for (p, b), n in vc.head(6).items()]
R["group_places"] = ex
R["year_booth"] = "1898 to 1899"
R["pop_per_lsoa"] = round(R["n"]["pop2022"] / R["n"]["lsoa_analysis"], -1)
R["fallen_hic"] = sum(R["groups"]["fallen"]["boroughs"].get(b, 0) for b in ("Hackney", "Islington", "Camden"))
fly = {}
for g, pl in (("persistent", "Bethnal Green"), ("persistent", "Lisson Grove"), ("turned", "Nine Elms"), ("fallen", "South Hackney")):
    G = A[(A.group == g) & (A.place == pl)]
    fly[pl] = [round(float(G.lon.mean()), 4), round(float(G.lat.mean()), 4)]
R["fly"] = fly
# Point correlations quoted at 2 dp are recomputed at 4 dp here so that 3-dp values ending in 5 are not rounded twice
# (models.json keeps 3 dp). Same data and formulas as 06_models.py.
from scipy.stats import spearmanr
sp = lambda D, x: round(float(spearmanr(D[x], D.imd_score).statistic), 4)
R["exploratory"]["rich_share"]["rho"]["rho"] = sp(A, "rich_share")
R["exploratory"]["yellow_share"]["rho"]["rho"] = sp(A, "yellow_share")
loo4 = [sp(A[A.lad24nm != r["left_out"]], "poor_share") for r in Mo["loo"]["rows"]]
R["loo"]["rho_min"], R["loo"]["rho_max"] = min(loo4), max(loo4)
# the planned exposure and sample variants other than purple-as-poor and the Thames split (R3, R4, R5)
core = [r for r in R["robust"] if r["label"][:2] in ("R3", "R4", "R5")]
R["robust_core"] = {"rho_min": min(r["rho"] for r in core), "rho_max": max(r["rho"] for r in core)}
# neighbourhoods with the most LSOAs where at least half the classified street was yellow (exploratory)
Y = A[(A.yellow_share >= 0.5) & (A.place != "")]
R["exploratory"]["yellow_ge_half_places"] = [{"place": p, "n": int(n)} for p, n in Y.place.value_counts().head(8).items()]
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("streets", "group_places", "robust_range", "shift_drop_1km_pc", "fe_full_range_sd")}, indent=1))
