"""Step 6: the pre-specified analysis (NOTES.md). Outputs data/models.json (every estimate) and data/lsoa_analysis.csv (the
analysis sample with BNG centroids, quintiles and groups)."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr, rankdata
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import shape
from common import *

rng = np.random.default_rng(2026)
B = int(os.environ.get("BT_BOOT", 2000))
O = pd.read_csv(f"{DATA}/lsoa_booth.csv")
geo = {}
import glob
for f in glob.glob(f"{LSOA_DIR}/E09*.geojson"):
    for ft in jload(f)["features"]:
        c = shape(ft["geometry"]).representative_point()
        geo[ft["properties"]["LSOA21CD"]] = (c.x, c.y)
tr = Transformer.from_crs(4326, 27700, always_xy=True)
O["lon"] = O.lsoa21cd.map(lambda c: geo[c][0]); O["lat"] = O.lsoa21cd.map(lambda c: geo[c][1])
O["E"], O["N"] = tr.transform(O.lon.values, O.lat.values)


def eligible(D, cov=0.9, minm=300):
    return D[(D.coverage >= cov) & (D.classified_m >= minm)].copy()


A = eligible(O)
A["block"] = (A.E // 1000).astype(int).astype(str) + "_" + (A.N // 1000).astype(int).astype(str)
A["poor10"] = A.poor_share * 10
A["imd_z"] = (A.imd_score - A.imd_score.mean()) / A.imd_score.std()
R = {"n": {"lsoa_london": int(len(O)), "lsoa_touching": int((O.coverage > 0).sum()), "lsoa_cov90": int((O.coverage >= 0.9).sum()),
           "lsoa_analysis": int(len(A)), "blocks": int(A.block.nunique()), "msoa": int(A.msoa.nunique()),
           "boroughs": int(A.lad24cd.nunique()), "pop2022": int(A.pop2022.sum())}}


def rho_ci(x, y, blocks, B=B):
    r = spearmanr(x, y).statistic
    ub = np.unique(blocks); idx = {b: np.where(blocks == b)[0] for b in ub}
    bs = []
    for _ in range(B):
        take = np.concatenate([idx[b] for b in rng.choice(ub, len(ub), replace=True)])
        bs.append(spearmanr(x[take], y[take]).statistic)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"rho": round(float(r), 3), "lo": round(float(lo), 3), "hi": round(float(hi), 3), "n": int(len(x))}


def fe_model(D, x="poor10", y="imd_score"):
    m = smf.ols(f"{y} ~ {x} + C(lad24cd)", data=D).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.msoa)[0]})
    b, se = m.params[x], m.bse[x]; lo, hi = m.conf_int().loc[x]
    m0 = smf.ols(f"{y} ~ {x}", data=D).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.msoa)[0]})
    return {"b": round(float(b), 3), "se": round(float(se), 3), "lo": round(float(lo), 3), "hi": round(float(hi), 3),
            "p": float(m.pvalues[x]), "n": int(m.nobs), "r2": round(float(m.rsquared), 3), "r2_within_add": None,
            "b_nofe": round(float(m0.params[x]), 3), "lo_nofe": round(float(m0.conf_int().loc[x][0]), 3),
            "hi_nofe": round(float(m0.conf_int().loc[x][1]), 3), "r2_nofe": round(float(m0.rsquared), 3), "_m": m}


def moran(v, xy, k=8, perm=999):
    t = cKDTree(xy); _, nn = t.query(xy, k + 1); nn = nn[:, 1:]
    z = v - v.mean()
    I = (z * z[nn].mean(1)).sum() / (z * z).sum()
    sims = []
    for _ in range(perm):
        zp = rng.permutation(z)
        sims.append((zp * zp[nn].mean(1)).sum() / (zp * zp).sum())
    p = (1 + np.sum(np.array(sims) >= I)) / (perm + 1)
    return {"I": round(float(I), 3), "p": float(p)}


xy = A[["E", "N"]].values
blocks = A.block.values
# main 1
R["main_rho"] = rho_ci(A.poor_share.values, A.imd_score.values, blocks)
# main 2
M2 = fe_model(A); m2 = M2.pop("_m")
R["main_fe"] = M2
Mz = fe_model(A, y="imd_z"); Mz.pop("_m"); R["main_fe_z"] = Mz
A["resid"] = m2.resid
# main 3
R["moran"] = {"booth": moran(A.poor_share.values, xy), "imd": moran(A.imd_score.values, xy), "resid": moran(A.resid.values, xy)}
# spatial error model (planned if residual Moran's I is clearly positive)
try:
    import libpysal, spreg
    w = libpysal.weights.KNN.from_array(xy, k=8); w.transform = "r"
    Xd = pd.get_dummies(A.lad24cd, drop_first=True).astype(float)
    Xd = Xd.loc[:, Xd.sum() >= 2]
    X = np.c_[A.poor10.values, Xd.values]
    se = spreg.ML_Error(A.imd_score.values[:, None], X, w=w, name_x=["poor10"] + list(Xd.columns))
    i = 1
    R["spatial_error"] = {"b": round(float(se.betas[i][0]), 3), "se": round(float(se.std_err[i]), 3),
                          "lo": round(float(se.betas[i][0] - 1.96 * se.std_err[i]), 3), "hi": round(float(se.betas[i][0] + 1.96 * se.std_err[i]), 3),
                          "lambda": round(float(se.betas[-1][0]), 3), "n": int(se.n)}
except Exception as e:
    R["spatial_error"] = {"error": str(e)[:200]}

# robustness
rob = []


def add(label, D, x, y="imd_score", plan=True, rank=False):
    D = D[D[x].notna()].copy()
    D["xx"] = D[x] * (10 if x.endswith("share") else 1)
    r = rho_ci(D[x].values, D[y].values, D.block.values if "block" in D else None, B=500) if "block" in D else None
    f = fe_model(D, x="xx", y=y); f.pop("_m")
    rob.append({"label": label, "x": x, "y": y, "planned": plan, "rho": r, "fe": f})


add("R1 purple counted as poor", A, "poor_purple_share")
add("R2 mean Booth score (1 black to 7 yellow)", A, "mean_score")
add("R3 map area instead of streets", A, "area_poor_share")
A4 = A[(A.hp_m >= 300)].copy()
add("R4 streets with purity at least 0.6", A4, "hp_poor_share")
A5 = eligible(O, 0.999, 500)
A5 = A.loc[A.lsoa21cd.isin(A5.lsoa21cd)]
add("R5 fully covered, at least 500 m classified", A5, "poor_share")
add("R6a income domain score", A, "poor_share", y="income_score")
A["imd_rank_rev"] = -A.imd_rank
add("R6b IMD national rank (most deprived high)", A, "poor_share", y="imd_rank_rev")
An = A[A.N > 0]
# Thames: north/south by borough
south = {"Southwark", "Lambeth", "Wandsworth", "Lewisham", "Greenwich", "Richmond upon Thames"}
add("R8a north of the Thames", A[~A.lad24nm.isin(south)], "poor_share")
add("R8b south of the Thames", A[A.lad24nm.isin(south)], "poor_share")
add("R8c without the City of London", A[A.lad24nm != "City of London"], "poor_share")
add("Window-mode classifier (first version)", A[A.wmode_m >= 300], "wmode_poor_share", plan=False)
R["robust"] = rob
# exploratory (not in the plan): the wealthy end of Booth's scale
A["rich_share"] = (A.m_red + A.m_yellow) / A.classified_m
A["yellow_share"] = A.m_yellow / A.classified_m
expl = {}
for nm in ("rich_share", "yellow_share"):
    D = A.copy(); D["xx"] = D[nm] * 10
    f = fe_model(D, x="xx"); f.pop("_m")
    expl[nm] = {"rho": rho_ci(D[nm].values, D.imd_score.values, D.block.values, B=500), "fe": f}
expl["has_yellow_n"] = int((A.m_yellow > 0).sum())
expl["yellow_ge_half_n"] = int((A.yellow_share >= 0.5).sum())
expl["yellow_ge_half_d12"] = int(((A.yellow_share >= 0.5) & (A.imd_decile <= 2)).sum())
expl["yellow_ge_half_d_ge8"] = int(((A.yellow_share >= 0.5) & (A.imd_decile >= 8)).sum())
expl["yellow_ge_half_mean_imd"] = round(float(A.imd_score[A.yellow_share >= 0.5].mean()), 2)
R["exploratory"] = expl
# R7 leave one borough out (boroughs with at least 20 LSOAs)
loo = []
for b, n in A.lad24nm.value_counts().items():
    if n < 20:
        continue
    D = A[A.lad24nm != b]
    f = fe_model(D); f.pop("_m")
    loo.append({"left_out": b, "rho": round(float(spearmanr(D.poor_share, D.imd_score).statistic), 3), "b": f["b"], "lo": f["lo"], "hi": f["hi"]})
R["loo"] = {"rows": loo, "rho_min": min(r["rho"] for r in loo), "rho_max": max(r["rho"] for r in loo),
            "b_min": min(r["b"] for r in loo), "b_max": max(r["b"] for r in loo)}

# descriptive: quintiles of Booth poverty x national IMD deciles
# Deviation from the plan, forced by ties: 579 LSOAs (47%) have no poor street at all, so quintiles 1 and 2 cannot be formed.
# Group 1 = no poor street; groups 2 to 5 = quartiles of the LSOAs with some. The "poorest fifth" used for the persistent and
# turned-around groups is the top 20% by Booth poverty share (no ties there); "fallen" uses group 1 (no poor street).
pos = A.poor_share > 0
A["bq"] = 1
A.loc[pos, "bq"] = pd.qcut(A.poor_share[pos], 4, labels=[2, 3, 4, 5]).astype(int)
A["top20"] = A.poor_share.rank(method="first", ascending=False) <= round(len(A) * 0.2)
ct = pd.crosstab(A.bq, A.imd_decile)
R["crosstab"] = {str(q): {str(d): int(ct.loc[q, d]) if d in ct.columns else 0 for d in range(1, 11)} for q in range(1, 6)}
R["quintile_cut"] = [round(float(A.poor_share[A.bq == q].min()), 4) for q in range(1, 6)]
R["quintile_mean_imd"] = {str(q): round(float(A.imd_score[A.bq == q].mean()), 2) for q in range(1, 6)}
R["quintile_share_d12"] = {str(q): round(float((A.imd_decile[A.bq == q] <= 2).mean() * 100), 1) for q in range(1, 6)}
A["group"] = np.select([A.top20 & (A.imd_decile <= 2), A.top20 & (A.imd_decile >= 6), (A.bq == 1) & (A.imd_decile <= 2)],
                       ["persistent", "turned", "fallen"], "")
grp = {}
for g in ["persistent", "turned", "fallen"]:
    G = A[A.group == g]
    grp[g] = {"n": int(len(G)), "boroughs": {k: int(v) for k, v in G.lad24nm.value_counts().items()}}
R["groups"] = grp
R["bq_n"] = {str(q): int((A.bq == q).sum()) for q in range(1, 6)}
R["top20_n"] = int(A.top20.sum())
R["top20_min"] = round(float(A.poor_share[A.top20].min() * 100), 1)
R["imd_d12_share_all"] = round(float((A.imd_decile <= 2).mean() * 100), 1)
R["imd_d1_n"] = int((A.imd_decile == 1).sum())
R["poor_share_mean"] = round(float(A.poor_share.mean() * 100), 1)
R["lsoa_no_poor"] = int((A.poor_share == 0).sum())

A.drop(columns=["resid"]).assign(resid=np.round(m2.resid, 3)).to_csv(f"{DATA}/lsoa_analysis.csv", index=False)
jsave(R, f"{DATA}/models.json", indent=1)
print(json.dumps({k: R[k] for k in ["n", "main_rho", "main_fe", "moran", "spatial_error"]}, indent=1, default=str))
for r in rob:
    print(r["label"], r["rho"], r["fe"]["b"], r["fe"]["lo"], r["fe"]["hi"], r["fe"]["n"])
print(R["loo"]["rho_min"], R["loo"]["rho_max"], R["loo"]["b_min"], R["loo"]["b_max"])
print(ct); print(R["quintile_mean_imd"], grp)
print(json.dumps(expl, indent=1, default=str))
