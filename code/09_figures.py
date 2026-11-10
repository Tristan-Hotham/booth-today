"""Step 9: figures for the paper (release/paper/f_*.pdf), the blog (release/blog/b_*.png, 1800 px) and the page (img/*.jpg),
plus header.png (1200 x 630). Every number drawn comes from data/results.json or the derived data files."""
import io
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.lines import Line2D
from PIL import Image
from figstyle import *

R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
A = pd.read_csv(f"{DATA}/lsoa_analysis.csv")
O = pd.read_csv(f"{DATA}/lsoa_booth.csv")
GJ = jload(f"{DATA}/lsoa_london.geojson")
K = np.cos(np.radians(51.51))
EXT = (-0.258, 0.011, 51.447, 51.567)


def lines(df):
    segs, cols = [], []
    for c, b in zip(df.coords, df.booth):
        xy = np.array([[float(v) for v in p.split()] for p in c.split(";")])
        segs.append(xy); cols.append(CLASS_HEX[b])
    return segs, cols


def polys(codes, colours, ec="none", lw=0.0):
    ps, cs = [], []
    for ft in GJ["features"]:
        c = ft["properties"]["c"]
        if c not in colours:
            continue
        g = ft["geometry"]
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        for r in rings:
            ps.append(MPoly(np.array(r), closed=True)); cs.append(colours[c])
    return PatchCollection(ps, facecolor=cs, edgecolor=ec, linewidth=lw)


def mapax(ax, ext=EXT):
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect(1 / K)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_facecolor(PAPER)


cl = S[S.booth != ""]
SEG, COL = lines(cl)
LW = {"primary": 1.1, "trunk": 1.1, "secondary": 1.0}

# ---------------- 1. the two maps ----------------
fig, axs = plt.subplots(1, 2, figsize=(14, 7.8), facecolor=PAPER)
ax = axs[0]; mapax(ax)
ax.add_collection(LineCollection(SEG, colors=COL, linewidths=0.55))
ax.set_title("Booth's colours, 1898 to 1899, read along today's streets", fontproperties=DISPB, fontsize=13.5, color=FG, loc="left")
h = [Line2D([], [], color=CLASS_HEX[c], lw=3.5, label=f"{CLASS_LABEL[c]}: {CLASS_NAME[c].split('.')[0]}") for c in CLASSES]
ax.legend(handles=h, loc="upper left", bbox_to_anchor=(0, -0.01), ncol=2, fontsize=8.5, frameon=False, handlelength=1.6)  # on paper, below the map
ax = axs[1]; mapax(ax)
dc = {r.lsoa21cd: DEC[int(r.imd_decile) - 1] for r in O[O.coverage > 0].itertuples()}
ax.add_collection(polys(None, dc, ec="#FFFFFF", lw=0.15))
an = {c: "none" for c in A.lsoa21cd}
pc = polys(None, {c: (0, 0, 0, 0) for c in A.lsoa21cd}, ec="none")
ax.set_title("Index of Multiple Deprivation 2025, by LSOA", fontproperties=DISPB, fontsize=13.5, color=FG, loc="left")
h = [Patch(facecolor=DEC[i], edgecolor=EDGE, label={0: "1: most deprived 10% in England", 9: "10: least deprived 10%"}.get(i, str(i + 1))) for i in range(10)]
ax.legend(handles=h, loc="upper left", bbox_to_anchor=(0, -0.01), ncol=3, fontsize=8.5, frameon=False, title="National decile (LSOAs touching Booth's map)", title_fontsize=8.5, alignment="left")
fig.text(0.01, 0.01, "Booth map: LSOA Library, Charles Booth's London (Public Domain Mark), via Layers of London. Streets: OpenStreetMap (ODbL). IMD 2025: MHCLG (OGL). LSOAs: ONS (OGL).".replace("LSOA Library", "LSE Library"),
         fontsize=7.5, color=MUT)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.subplots_adjust(bottom=0.27)
savefig(fig, "map", blog="map", img="map")

# ---------------- 2. method: the printed map and the reading ----------------
from common import Tiles
T = Tiles()
lon0, lat0 = -0.0735, 51.5185
X, Y = ll2px(lon0, lat0); X, Y = int(X), int(Y)
RW, RH = 300, 200
crop = np.full((2 * RH, 2 * RW, 3), 255, np.uint8)
for ty in range((Y - RH) // 256, (Y + RH) // 256 + 1):
    for tx in range((X - RW) // 256, (X + RW) // 256 + 1):
        a = T.get(tx, ty)
        if a is None:
            continue
        x0 = max(tx * 256, X - RW); x1 = min(tx * 256 + 256, X + RW); y0 = max(ty * 256, Y - RH); y1 = min(ty * 256 + 256, Y + RH)
        crop[y0 - (Y - RH):y1 - (Y - RH), x0 - (X - RW):x1 - (X - RW)] = a[y0 - ty * 256:y1 - ty * 256, x0 - tx * 256:x1 - tx * 256, :3]
lo0, la1 = px2ll(X - RW, Y - RH); lo1, la0 = px2ll(X + RW, Y + RH)
ext = (float(lo0), float(lo1), float(la0), float(la1))
fig, axs = plt.subplots(1, 2, figsize=(14, 5.0), facecolor=PAPER)
axs[0].imshow(crop, extent=ext, aspect=1 / K); mapax(axs[0], ext)
axs[0].set_title("The printed map (Spitalfields and Whitechapel)", fontproperties=DISPB, fontsize=13, color=FG, loc="left")
mapax(axs[1], ext)
sub = cl[(cl.lon > ext[0] - 0.005) & (cl.lon < ext[1] + 0.005) & (cl.lat > ext[2] - 0.005) & (cl.lat < ext[3] + 0.005)]
sg, sc = lines(sub)
axs[1].add_collection(LineCollection(sg, colors=sc, linewidths=3.2, capstyle="round"))
un = S[(S.booth == "") & (S.lon > ext[0] - 0.005) & (S.lon < ext[1] + 0.005) & (S.lat > ext[2] - 0.005) & (S.lat < ext[3] + 0.005)]
ug = [np.array([[float(v) for v in p.split()] for p in c.split(";")]) for c in un.coords]
axs[1].add_collection(LineCollection(ug, colors="#C9C2B4", linewidths=1.0))
axs[1].set_title("Read along today's OpenStreetMap streets", fontproperties=DISPB, fontsize=13, color=FG, loc="left")
h = [Line2D([], [], color=CLASS_HEX[c], lw=4, label=CLASS_LABEL[c]) for c in CLASSES] + [Line2D([], [], color="#C9C2B4", lw=1.5, label="no colour read")]
axs[1].legend(handles=h, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
fig.tight_layout()
savefig(fig, "method", blog="method", img="method")

# ---------------- 3. two ends of the scale ----------------
fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=PAPER, sharey=True)
A["rich"] = (A.m_red + A.m_yellow) / A.classified_m
bins = [0, 0.0001, 0.05, 0.1, 0.2, 0.4, 0.6, 1.0001]
labs = ["none", "under 5%", "5 to 10%", "10 to 20%", "20 to 40%", "40 to 60%", "60% or more"]
for ax, col, var, ttl in ((axs[0], CLASS_HEX["dkblue"], "poor_share", "Share of street Booth coloured black or blue"),
                          (axs[1], CLASS_HEX["red"], "rich", "Share of street Booth coloured red or yellow")):
    A["bin"] = pd.cut(A[var], bins, right=False, labels=labs)
    g = A.groupby("bin", observed=False).imd_score.agg(["mean", "std", "count"])
    se = g["std"] / np.sqrt(g["count"])
    x = np.arange(len(g))
    ax.scatter(np.interp(A[var], [0, 0.0001, 0.05, 0.1, 0.2, 0.4, 0.6, 1], [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]) - 0.5 + np.random.default_rng(1).uniform(-0.3, 0.3, len(A)),
               A.imd_score, s=5, color=col, alpha=0.16, lw=0, rasterized=True)
    ax.errorbar(x, g["mean"], yerr=1.96 * se, fmt="o", color=FG, ms=7, capsize=3, lw=1.6, zorder=5)
    for xi, n in zip(x, g["count"]):
        ax.text(xi, 2, f"n={n}", ha="center", fontsize=7.5, color=MUT)
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.5, rotation=20)
    ax.set_title(ttl, fontproperties=DISPB, fontsize=12.5, color=FG, loc="left")
    style_axes(ax); ax.set_facecolor(PAPER)
axs[0].set_ylabel("IMD 2025 score (higher = more deprived)")
axs[0].set_ylim(0, 60)
fig.text(0.01, 0.01, f"{R['n']['lsoa_analysis']:,} LSOAs on Booth's map. Black dots: mean and 95% interval; coloured dots: LSOAs.", fontsize=8, color=MUT)
fig.tight_layout(rect=(0, 0.03, 1, 1))
savefig(fig, "ends", blog="ends", img="ends")

# ---------------- 4. quintile x decile ----------------
ct = np.array([[R["crosstab"][str(q)][str(d)] for d in range(1, 11)] for q in range(1, 6)], float)
pct = ct / ct.sum(1, keepdims=True) * 100
fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=PAPER)
im = ax.imshow(pct, cmap=ListedColormap(["#F7F1E6", "#E9D9BE", "#D7BC93", "#BF9866", "#9C7240", "#6F4C25"]), vmin=0, vmax=30, aspect="auto")
for i in range(5):
    for j in range(10):
        ax.text(j, i, f"{pct[i, j]:.0f}", ha="center", va="center", fontsize=9, color=FG if pct[i, j] < 20 else "white")
ax.set_xticks(range(10)); ax.set_xticklabels([str(d) for d in range(1, 11)])
ax.set_yticks(range(5)); ax.set_yticklabels(["1 (no poor street)", "2", "3", "4", "5 (most poor)"])
ax.set_xlabel("IMD 2025 national decile (1 = most deprived 10% in England)")
ax.set_ylabel("Booth poverty group")
ax.set_title("Where Booth's poverty groups sit today (% of LSOAs in each row)", fontproperties=DISPB, fontsize=12.5, color=FG, loc="left")
fig.tight_layout()
savefig(fig, "crosstab", blog="crosstab", img="crosstab")

# ---------------- 5. shift test ----------------
Sh = jload(f"{DATA}/shift.json")
rows = pd.DataFrame(Sh["rows"])
fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=PAPER)
ds = [0, 500, 1000, 2000, 4000]
for var, col, lab in (("rho", CLASS_HEX["dkblue"], "Booth poverty share (black and blue)"), ("rho_score", CLASS_HEX["red"], "Booth mean score (sign flipped)")):
    sgn = -1 if var == "rho_score" else 1
    m = [sgn * rows[rows.dist == d][var].mean() for d in ds]
    lo = [sgn * rows[rows.dist == d][var].min() for d in ds]; hi = [sgn * rows[rows.dist == d][var].max() for d in ds]
    lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
    ax.fill_between(range(5), lo, hi, color=col, alpha=0.15, lw=0)
    ax.plot(range(5), m, "-o", color=col, lw=2, ms=7, label=lab)
ax.axhline(0, color=MUT, lw=0.8)
ax.set_xticks(range(5)); ax.set_xticklabels(["true place", "500 m", "1 km", "2 km", "4 km"])
ax.set_xlabel("Booth's map slid away from each LSOA by")
ax.set_ylabel("Rank correlation with IMD 2025")
ax.legend(frameon=False, fontsize=9)
style_axes(ax); ax.set_facecolor(PAPER)
ax.set_title("Move the old map 1 km and the link mostly goes", fontproperties=DISPB, fontsize=12.5, color=FG, loc="left")
fig.tight_layout()
savefig(fig, "shift", blog="shift", img="shift")

# ---------------- 6. groups map ----------------
GC = {"persistent": "#4A1426", "turned": "#2F7FB8", "fallen": "#D08A1E"}
fig, ax = plt.subplots(figsize=(10, 7.4), facecolor=PAPER); mapax(ax, (-0.258, 0.011, 51.405, 51.567))
ax.add_collection(polys(None, {c: "#ECE6DA" for c in A.lsoa21cd}, ec="#FFFFFF", lw=0.2))
ax.add_collection(polys(None, {r.lsoa21cd: GC[r.group] for r in A[A.group.isin(list(GC))].itertuples()}, ec="#FFFFFF", lw=0.2))
ax.add_collection(LineCollection(SEG, colors="#00000010", linewidths=0.3))
G = R["groups"]
h = [Patch(facecolor=GC["persistent"], label=f"Poorest fifth then, most deprived 20% now ({G['persistent']['n']})"),
     Patch(facecolor=GC["turned"], label=f"Poorest fifth then, least deprived half now ({G['turned']['n']})"),
     Patch(facecolor=GC["fallen"], label=f"No poor street then, most deprived 20% now ({G['fallen']['n']})"),
     Patch(facecolor="#ECE6DA", label="Other LSOAs in the analysis")]
ax.legend(handles=h, loc="lower left", fontsize=8.5, frameon=False, ncol=2)
ax.set_title("Stuck, turned around and fallen", fontproperties=DISPB, fontsize=14, color=FG, loc="left")
fig.tight_layout()
savefig(fig, "groups", blog="groups", img="groups")

# ---------------- 7. robustness forest ----------------
rb = [{"label": "Main: Booth poverty share", "rho": R["main_rho"]["rho"], "lo": R["main_rho"]["lo"], "hi": R["main_rho"]["hi"], "n": R["main_rho"]["n"]}]
for r in R["robust"]:
    if r["x"] == "mean_score":
        continue
    rb.append({"label": r["label"], "rho": r["rho"], "lo": r["rho_lo"], "hi": r["rho_hi"], "n": r["n"]})
fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=PAPER)
for i, r in enumerate(rb):
    y = len(rb) - 1 - i
    ax.plot([r["lo"], r["hi"]], [y, y], color=FG, lw=1.6)
    ax.plot(r["rho"], y, "o", color=HOT if i == 0 else FG, ms=7)
ax.set_yticks(range(len(rb))); ax.set_yticklabels([f"{r['label']} (n={r['n']:,})" for r in rb][::-1], fontsize=8.5)
ax.axvline(0, color=MUT, lw=0.8)
ax.set_xlabel("Spearman rank correlation with IMD 2025 (95% interval, block bootstrap)")
style_axes(ax); ax.grid(axis="x", color=RULE, lw=0.6); ax.grid(axis="y", visible=False); ax.set_facecolor(PAPER)
ax.set_title("The main result and the planned checks", fontproperties=DISPB, fontsize=12.5, color=FG, loc="left")
fig.tight_layout()
savefig(fig, "robust", blog="robust", img="robust")

# ---------------- header 1200 x 630 ----------------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.40, 0.02, 0.59, 0.96]); mapax(ax, (-0.20, -0.02, 51.475, 51.555))
ax.add_collection(LineCollection(SEG, colors=COL, linewidths=0.9))
fig.text(0.04, 0.80, "Booth's poverty", fontproperties=DISP, fontsize=40, color=FG)
fig.text(0.04, 0.70, "map today", fontproperties=DISP, fontsize=40, color=HOT)
fig.text(0.04, 0.56, "Are London's poorest streets of\nthe 1890s still the poorest?", fontproperties=SERP, fontsize=17, color=FG, linespacing=1.3)
fig.text(0.04, 0.38, f"Rank correlation with deprivation\ntoday: {R['main_rho']['rho']:.2f} across {R['n']['lsoa_analysis']:,} areas", fontsize=12.5, color=MUT, linespacing=1.4)
for i, c in enumerate(CLASSES):
    fig.patches.append(plt.Rectangle((0.04 + i * 0.045, 0.24), 0.04, 0.035, transform=fig.transFigure, color=CLASS_HEX[c]))
fig.text(0.04, 0.19, "black, blues: poor   purple: mixed", fontsize=8.5, color=MUT)
fig.text(0.04, 0.155, "pink, red, yellow: comfortable to wealthy", fontsize=8.5, color=MUT)
fig.text(0.04, 0.06, "maps.tristanhotham.com/booth-today", fontsize=11, color=FG)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
print(Image.open(os.path.join(ROOT, "header.png")).size, sorted(os.listdir(f"{REL}/blog")))
