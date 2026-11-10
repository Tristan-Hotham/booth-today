"""Step 3: read Booth's colour along every OpenStreetMap street.

Each way is walked every STEP px (zoom 16, about 1.49 m per px); at each position, 7 x 7 px windows are read at OFFS px to
each side of the centreline (house frontages, not the roadway) and classified by winrule.classify. The first and last END px
of each way are skipped (junctions). Outputs:
  SCR/positions.npz     one row per position: way index, lon, lat, 8 window codes (kept in scratch; used by step 4)
  data/streets_booth.csv.gz  one row per way: osm id, name, highway, length, windows, coloured windows, pooled pixel counts
                        of the seven inks, Booth colour (classify_pooled), purity (share of the coloured ink in the winning
                        colour's ink group), Booth score 1 to 7, and the window-mode colour (sensitivity)."""
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from common import *
from winrule import classify, fractions, CODE, colour_mask, classify_pooled, INKS7, pool_counts

STEP, END, OFFS, HW = 3.0, 10.0, (5, 7, 9, 11), 3
MIN_COL = 4
d = np.load(f"{SCR}/inks.npz"); M = d["M"]; X0 = int(d["X0"]) * 256; Y0 = int(d["Y0"]) * 256
H, W = M.shape
S = pd.read_csv(f"{DATA}/streets.csv.gz", keep_default_na=False)

wid, plon, plat, PX, PY = [], [], [], [], []
for i, c in enumerate(S.coords.values):
    xy = np.array([[float(v) for v in p.split()] for p in c.split(";")])
    X, Y = ll2px(xy[:, 0], xy[:, 1])
    seg = np.hypot(np.diff(X), np.diff(Y)); cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 2 * END:
        continue
    t = np.arange(END, cum[-1] - END + 1e-9, STEP)
    j = np.clip(np.searchsorted(cum, t, side="right") - 1, 0, len(seg) - 1)
    ok = seg[j] > 0
    t, j = t[ok], j[ok]
    fr = (t - cum[j]) / seg[j]
    px = X[j] + fr * (X[j + 1] - X[j]); py = Y[j] + fr * (Y[j + 1] - Y[j])
    nx = -(Y[j + 1] - Y[j]) / seg[j]; ny = (X[j + 1] - X[j]) / seg[j]
    lo, la = px2ll(px, py)
    wid.append(np.full(len(t), i, np.int32)); plon.append(lo); plat.append(la)
    PX.append(px[:, None] + nx[:, None] * np.r_[OFFS, [-o for o in OFFS]][None, :])
    PY.append(py[:, None] + ny[:, None] * np.r_[OFFS, [-o for o in OFFS]][None, :])
wid = np.concatenate(wid); plon = np.concatenate(plon); plat = np.concatenate(plat)
PX = np.concatenate(PX); PY = np.concatenate(PY)
print(len(wid), "positions")

codes = np.full(PX.shape, -2, np.int8)          # window-level colour (kept for the window-mode sensitivity check)
INKC = np.zeros((PX.shape[0], 7), np.int32)      # per position: pooled pixel counts of the 7 Booth inks over coloured windows
NCOL = np.zeros(PX.shape[0], np.int16)           # per position: coloured windows (of 8)
cx = np.round(PX).astype(np.int64) - X0; cy = np.round(PY).astype(np.int64) - Y0
inside = (cx >= HW) & (cx < W - HW) & (cy >= HW) & (cy < H - HW)
dy, dx = np.mgrid[-HW:HW + 1, -HW:HW + 1]
for k in range(0, PX.shape[0], 50000):
    sl = slice(k, k + 50000)
    ok = inside[sl]
    win = np.zeros(ok.shape + (49,), np.uint8)
    yy = np.where(ok, cy[sl], HW); xx = np.where(ok, cx[sl], HW)
    win = M[yy[..., None] + dy.ravel(), xx[..., None] + dx.ravel()]
    win[~ok] = 0
    F = fractions(win.reshape(-1, 49))
    cm = colour_mask(F).reshape(ok.shape)
    codes[sl] = classify(F).reshape(ok.shape)
    cnt = pool_counts(F).reshape(ok.shape + (7,))
    INKC[sl] = (cnt * cm[..., None]).sum(1)
    NCOL[sl] = cm.sum(1)
np.savez_compressed(f"{SCR}/positions.npz", wid=wid, lon=plon.astype(np.float32), lat=plat.astype(np.float32), codes=codes,
                    inkc=INKC, ncol=NCOL)

# per way: pool the ink counts of all coloured windows, then classify (classify_pooled)
n_pos = np.bincount(wid, minlength=len(S))
pool = np.stack([np.bincount(wid, weights=INKC[:, k], minlength=len(S)) for k in range(7)], 1)
ncol = np.bincount(wid, weights=NCOL, minlength=len(S)).astype(int)
nwin = np.bincount(wid, weights=inside.sum(1), minlength=len(S)).astype(int)
cls, pur = classify_pooled(pool)
mode = np.where(ncol >= MIN_COL, cls, -1)
conf = np.where(ncol >= MIN_COL, pur, np.nan)
wc = np.stack([np.bincount(wid, weights=(codes == c).sum(1), minlength=len(S)) for c in range(7)], 1)
wmode = np.where(wc.sum(1) >= MIN_COL, wc.argmax(1), -1)
score = np.where(mode >= 0, mode + 1, np.nan)
cnt = pool.astype(int)
O = S[["osm_id", "name", "highway", "length_m", "lon", "lat"]].copy()
O["positions"] = n_pos; O["windows"] = nwin; O["coloured"] = ncol
for k, nm in enumerate(["black", "dkblue_ink", "ltblue_ink", "ochre", "red_ink", "mauve", "lightred"]):
    O[f"px_{nm}"] = cnt[:, k]
O["booth"] = [CODE[m] if m >= 0 else "" for m in mode]
O["purity"] = np.round(conf, 3); O["score"] = score
O["booth_window_mode"] = [CODE[m] if m >= 0 else "" for m in wmode]
O["coords"] = S.coords
O.to_csv(f"{DATA}/streets_booth.csv.gz", index=False)
cl = O[O.booth != ""]
print(len(cl), "of", len(O), "ways coloured;", round(cl.length_m.sum() / 1000), "km")
print((cl.groupby("booth").length_m.sum() / cl.length_m.sum() * 100).round(1).to_dict())
print("median purity", cl.purity.median())
