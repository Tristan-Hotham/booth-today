"""Step 5: Booth measures for every London LSOA 2021.

1. LSOA polygons (33 borough files, fetched by 00_fetch_lsoa.py into scratch) are rasterised onto the Booth pixel grid
   (zoom 16). Coverage = share of each LSOA's pixels that lie on the printed map (ink code > 0).
2. Each street sampling position takes the LSOA under its centreline point; a street "piece" is a way within one LSOA.
   Piece length = positions x 3 px x metres per px; piece colour from the pooled ink counts of its coloured windows
   (classify_pooled; at least 4 coloured windows).
3. LSOA measures (classified street length; poor share; poor share with purple; mean score; high-purity poor share;
   window-mode poor share; area-based poor share from all colour-ink pixels in the LSOA).
Outputs: data/lsoa_booth.csv (every London LSOA, with coverage and measures), data/lsoa_london.geojson (simplified polygons
of the LSOAs on the map, for the page and figures), SCR/lsoa_raster.npy and SCR/pos_lsoa.npy (for the shift test)."""
import glob
import numpy as np
import pandas as pd
from affine import Affine
from rasterio.features import rasterize
from scipy.ndimage import uniform_filter
from shapely.geometry import shape, mapping
from common import *
from winrule import classify_pooled, CODE

STEP = 3.0
MIN_COL = 4
d = np.load(f"{SCR}/inks.npz"); M = d["M"]; X0 = int(d["X0"]) * 256; Y0 = int(d["Y0"]) * 256
H, W = M.shape

feats = []
for f in sorted(glob.glob(f"{LSOA_DIR}/E09*.geojson")):
    feats += jload(f)["features"]
codes = [ft["properties"]["LSOA21CD"] for ft in feats]
assert len(codes) == len(set(codes)) == 4994, len(codes)


def to_px(geom):
    def tr(ring):
        a = np.asarray(ring)
        x, y = ll2px(a[:, 0], a[:, 1])
        return np.c_[x - X0, y - Y0].tolist()
    g = geom
    if g["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [tr(r) for r in g["coordinates"]]}
    return {"type": "MultiPolygon", "coordinates": [[tr(r) for r in p] for p in g["coordinates"]]}


def lsoa_raster(dx=0.0, dy=0.0):
    """LSOA index raster (-1 outside) with every polygon shifted by (dx, dy) pixels"""
    shapes = []
    for i, ft in enumerate(feats):
        g = to_px(ft["geometry"])
        if dx or dy:
            from shapely.affinity import translate
            g = mapping(translate(shape(g), dx, dy))
        shapes.append((g, i))
    return rasterize(shapes, out_shape=(H, W), fill=-1, transform=Affine.identity(), dtype="int32", all_touched=False)


def lsoa_pixels_total(dx=0.0, dy=0.0):
    """total pixel area of each LSOA (also off the mosaic), for coverage: computed from polygon area in pixel units"""
    out = np.zeros(len(feats))
    for i, ft in enumerate(feats):
        out[i] = shape(to_px(ft["geometry"])).area
    return out


def lsoa_measures(pl, P, mpp):
    keep = pl >= 0
    key = pd.DataFrame({"w": P["wid"][keep], "l": pl[keep], "m": mpp[keep] * STEP, "nc": P["ncol"][keep]})
    for k in range(7):
        key[f"c{k}"] = P["inkc"][keep][:, k]
    cw = P["codes"][keep]
    for c in range(7):
        key[f"w{c}"] = (cw == c).sum(1)
    g = key.groupby(["w", "l"], sort=False).sum().reset_index()
    cls, pur = classify_pooled(g[[f"c{k}" for k in range(7)]].values)
    g["cls"] = np.where(g.nc >= MIN_COL, cls, -1); g["pur"] = pur
    wc = g[[f"w{c}" for c in range(7)]].values
    g["wmode"] = np.where(wc.sum(1) >= MIN_COL, wc.argmax(1), -1)
    return g


def summarise(G, n):
    col = G.cls >= 0
    L = np.bincount(G.l[col], weights=G.m[col], minlength=n)
    Lp = np.bincount(G.l[col & G.cls.isin([0, 1, 2])], weights=G.m[col & G.cls.isin([0, 1, 2])], minlength=n)
    Lpp = np.bincount(G.l[col & G.cls.isin([0, 1, 2, 3])], weights=G.m[col & G.cls.isin([0, 1, 2, 3])], minlength=n)
    Ls = np.bincount(G.l[col], weights=G.m[col] * (G.cls[col] + 1), minlength=n)
    hp = col & (G.pur >= 0.6)
    Lh = np.bincount(G.l[hp], weights=G.m[hp], minlength=n)
    Lhp = np.bincount(G.l[hp & G.cls.isin([0, 1, 2])], weights=G.m[hp & G.cls.isin([0, 1, 2])], minlength=n)
    wc = G.wmode >= 0
    Lw = np.bincount(G.l[wc], weights=G.m[wc], minlength=n)
    Lwp = np.bincount(G.l[wc & G.wmode.isin([0, 1, 2])], weights=G.m[wc & G.wmode.isin([0, 1, 2])], minlength=n)
    Lall = np.bincount(G.l, weights=G.m, minlength=n)
    per = {c: np.bincount(G.l[G.cls == k], weights=G.m[G.cls == k], minlength=n) for k, c in enumerate(CODE)}
    with np.errstate(invalid="ignore", divide="ignore"):
        out = dict(street_m=Lall, classified_m=L, poor_share=Lp / L, poor_purple_share=Lpp / L, mean_score=Ls / L,
                   hp_m=Lh, hp_poor_share=Lhp / Lh, wmode_m=Lw, wmode_poor_share=Lwp / Lw)
    for c in CODE:
        out[f"m_{c}"] = per[c]
    return out


if __name__ == "__main__":
    LR = lsoa_raster()
    np.save(f"{SCR}/lsoa_raster.npy", LR)
    area_px = lsoa_pixels_total()
    on = M > 0
    n_on = np.bincount(LR[LR >= 0], minlength=len(feats))
    n_onmap = np.bincount(LR[(LR >= 0) & on], minlength=len(feats))
    coverage = np.minimum(n_onmap / np.maximum(area_px, 1), 1.0)

    # area-based (R3): colour-ink pixels per LSOA; black only where the 7 x 7 neighbourhood is at least half black
    solid_black = uniform_filter((M == 3).astype(np.float32), 7) >= 0.5
    poor_px = solid_black | (M == 4) | (M == 5)
    col_px = poor_px | np.isin(M, [6, 7, 8, 9])
    ok = LR >= 0
    a_col = np.bincount(LR[ok & col_px], minlength=len(feats))
    a_poor = np.bincount(LR[ok & poor_px], minlength=len(feats))

    # streets: positions to LSOAs
    P = np.load(f"{SCR}/positions.npz")
    px, py = ll2px(P["lon"].astype(float), P["lat"].astype(float))
    ix = np.clip(np.round(px).astype(int) - X0, 0, W - 1); iy = np.clip(np.round(py).astype(int) - Y0, 0, H - 1)
    pl = LR[iy, ix]
    np.save(f"{SCR}/pos_lsoa.npy", pl)
    mpp = 156543.03392 * np.cos(np.radians(P["lat"].astype(float))) / 2 ** Z
    S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False, usecols=["osm_id", "name", "highway"])


    G = lsoa_measures(pl, P, mpp)
    G.drop(columns=[c for c in G.columns if c.startswith(("c", "w")) and c not in ("cls", "w")]).to_csv(
        f"{SCR}/pieces.csv.gz", index=False)


    Sm = summarise(G, len(feats))
    D = pd.read_csv(DEPRIV)
    D = D.rename(columns={D.columns[0]: "lsoa21cd", D.columns[1]: "lsoa21nm", D.columns[2]: "lad24cd", D.columns[3]: "lad24nm",
                          D.columns[4]: "imd_score", D.columns[5]: "imd_rank", D.columns[6]: "imd_decile",
                          D.columns[7]: "income_score", D.columns[8]: "income_rank"})
    D = D[["lsoa21cd", "lsoa21nm", "lad24cd", "lad24nm", "imd_score", "imd_rank", "imd_decile", "income_score", "income_rank",
           "Total population: mid 2022"]].rename(columns={"Total population: mid 2022": "pop2022"})
    O = pd.DataFrame({"lsoa21cd": codes, "lsoa21nm_geo": [ft["properties"]["LSOA21NM"] for ft in feats],
                      "lad_geo": [ft["properties"]["LADCD_ACTIVE"] for ft in feats],
                      "coverage": np.round(coverage, 4), "area_px": np.round(area_px), "ink_px": a_col, "poor_px": a_poor})
    for k, v in Sm.items():
        O[k] = np.round(v, 5) if k.endswith(("share", "score")) else np.round(v, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        O["area_poor_share"] = np.round(a_poor / np.where(a_col > 0, a_col, np.nan), 5)
    O["km2"] = [round(shape(ft["geometry"]).area * 0, 4) for ft in feats]   # placeholder, filled below
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    O["km2"] = [round(abs(geod.geometry_area_perimeter(shape(ft["geometry"]))[0]) / 1e6, 4) for ft in feats]
    O = O.merge(D, on="lsoa21cd", how="left")
    assert O.imd_score.notna().all()
    O["msoa"] = O.lsoa21nm.str[:-1]
    O.to_csv(f"{DATA}/lsoa_booth.csv", index=False)
    # simplified polygons of LSOAs touching the map, for the page
    keep = set(O.lsoa21cd[O.coverage > 0])
    fs = []
    for ft in feats:
        if ft["properties"]["LSOA21CD"] in keep:
            g = shape(ft["geometry"]).simplify(0.00006, preserve_topology=True)
            gm = mapping(g)
            rnd = lambda r: [[round(x, 5), round(y, 5)] for x, y in r]
            if gm["type"] == "Polygon":
                c = [rnd(r) for r in gm["coordinates"]]
            else:
                c = [[rnd(r) for r in p] for p in gm["coordinates"]]
            fs.append({"type": "Feature", "properties": {"c": ft["properties"]["LSOA21CD"]}, "geometry": {"type": gm["type"], "coordinates": c}})
    jsave({"type": "FeatureCollection", "features": fs}, f"{DATA}/lsoa_london.geojson")
    el = O[(O.coverage >= 0.9) & (O.classified_m >= 300)]
    print("LSOAs touching map", (O.coverage > 0).sum(), "coverage>=0.9", (O.coverage >= 0.9).sum(), "eligible", len(el))
    print("pieces", len(G), "classified km", round(G.m[G.cls >= 0].sum() / 1000))
