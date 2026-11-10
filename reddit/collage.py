"""Reddit collage (r/dataisbeautiful style), light background: Booth's colours along today's streets, deprivation in 2025, the
scale test and the two ends of Booth's scale. Every number from data/results.json. Output reddit/booth_today_collage.png."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
A = pd.read_csv(f"{DATA}/lsoa_analysis.csv")
O = pd.read_csv(f"{DATA}/lsoa_booth.csv")
GJ = jload(f"{DATA}/lsoa_london.geojson")
Sh = pd.DataFrame(jload(f"{DATA}/shift.json")["rows"])
K = np.cos(np.radians(51.51)); EXT = (-0.258, 0.011, 51.447, 51.567)
cl = S[S.booth != ""]
seg = [np.array([[float(v) for v in p.split()] for p in c.split(";")]) for c in cl.coords]
col = [CLASS_HEX[b] for b in cl.booth]


def mapax(ax):
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3]); ax.set_aspect(1 / K); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_facecolor(PAPER)


fig = plt.figure(figsize=(16, 17.5), dpi=160, facecolor=PAPER)
fig.text(0.03, 0.965, "Booth's poverty map, then and now", fontproperties=DISP, fontsize=40, color=FG)
fig.text(0.03, 0.940, f"Charles Booth coloured every street of inner London in 1898 to 1899. I read his colours along {R['streets']['km_classified']:,} km of today's streets",
         fontproperties=SERP, fontsize=17, color=FG)
fig.text(0.03, 0.922, f"and compared them with deprivation in 2025 for {R['n']['lsoa_analysis']:,} small areas. The old pattern still shows, faintly, and only street by street.", fontproperties=SERP, fontsize=17, color=FG)

ax = fig.add_axes([0.02, 0.50, 0.47, 0.40]); mapax(ax)
ax.add_collection(LineCollection(seg, colors=col, linewidths=0.6))
ax.set_title("1898 to 1899: Booth's colours on today's streets", fontproperties=DISPB, fontsize=17, color=FG, loc="left")
ax = fig.add_axes([0.51, 0.50, 0.47, 0.40]); mapax(ax)
ps, cs = [], []
dec = dict(zip(O.lsoa21cd, O.imd_decile)); cov = dict(zip(O.lsoa21cd, O.coverage))
OFF = "#E4E0D8"  # LSOAs not on Booth's map
for ft in GJ["features"]:
    g = ft["geometry"]; rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
    for r in rings:
        ps.append(MPoly(np.array(r))); c0 = ft["properties"]["c"]; cs.append(DEC[int(dec[c0]) - 1] if cov.get(c0, 0) > 0 else OFF)
ax.add_collection(PatchCollection(ps, facecolor=cs, edgecolor="#FFFFFF", linewidth=0.12))
ax.set_title("2025: Index of Multiple Deprivation", fontproperties=DISPB, fontsize=17, color=FG, loc="left")

# legends on paper, below the maps
lg = fig.add_axes([0.02, 0.405, 0.47, 0.09]); lg.axis("off")
h = [Line2D([], [], color=CLASS_HEX[c], lw=6, label=f"{CLASS_LABEL[c]}: {CLASS_NAME[c].split('.')[0].lower()}") for c in CLASSES]
lg.legend(handles=h, loc="upper left", ncol=2, fontsize=11.5, frameon=False, handlelength=1.8, columnspacing=1.2)
lg2 = fig.add_axes([0.51, 0.405, 0.47, 0.09]); lg2.axis("off")
h = [Patch(facecolor=DEC[i], edgecolor=EDGE, label={0: "1: most deprived 10% of England", 9: "10: least deprived 10%"}.get(i, str(i + 1))) for i in range(10)]
lg2.legend(handles=h, loc="upper left", ncol=3, fontsize=11.5, frameon=False, title="National decile, 2025 (small areas touching Booth's map)", title_fontsize=11.5, alignment="left")

# bottom left: the two ends
ax = fig.add_axes([0.07, 0.10, 0.40, 0.26])
A["rich"] = (A.m_red + A.m_yellow) / A.classified_m
bins = [0, 0.0001, 0.1, 0.2, 0.4, 0.6, 1.0001]; labs = ["none", "<10%", "10-20%", "20-40%", "40-60%", "60%+"]
for var, c, nm, off in (("poor_share", CLASS_HEX["dkblue"], "Black or blue streets (poor)", -0.12), ("rich", CLASS_HEX["red"], "Red or yellow streets (well-off)", 0.12)):
    g = A.groupby(pd.cut(A[var], bins, right=False, labels=labs), observed=False).imd_score.agg(["mean", "std", "count"])
    se = g["std"] / np.sqrt(g["count"]); x = np.arange(len(g)) + off
    ax.errorbar(x, g["mean"], yerr=1.96 * se, fmt="-o", color=c, ms=9, lw=2.4, capsize=3, label=nm)
ax.set_xticks(range(len(labs))); ax.set_xticklabels(["none", "under 10%", "10 to 20%", "20 to 40%", "40 to 60%", "60% or more"], fontsize=11)
ax.set_xlabel("Share of the area's street in that colour in 1899", fontsize=12)
ax.set_ylabel("Deprivation score 2025 (higher = worse)", fontsize=12)
ax.legend(frameon=False, fontsize=12, loc="lower left")
style_axes(ax); ax.set_facecolor(PAPER)
ax.set_title("Exploratory: wealth seems to have stayed put", fontproperties=DISPB, fontsize=17, color=FG, loc="left")

# bottom right: shift test
ax = fig.add_axes([0.57, 0.10, 0.40, 0.26])
ds = [0, 500, 1000, 2000, 4000]
m = [Sh[Sh.dist == d].rho.mean() for d in ds]; lo = [Sh[Sh.dist == d].rho.min() for d in ds]; hi = [Sh[Sh.dist == d].rho.max() for d in ds]
ax.fill_between(range(5), lo, hi, color=CLASS_HEX["dkblue"], alpha=0.15, lw=0)
ax.plot(range(5), m, "-o", color=CLASS_HEX["dkblue"], lw=2.6, ms=10)
for i, v in enumerate(m):
    ax.text(i, v + 0.025, f"{v:.2f}", ha="center", fontsize=12, color=FG)
ax.axhline(0, color=MUT, lw=0.9)
ax.set_xticks(range(5)); ax.set_xticklabels(["in place", "500 m", "1 km", "2 km", "4 km"], fontsize=11)
ax.set_xlabel("Booth's map slid away from each area by", fontsize=12)
ax.set_ylabel("Rank correlation, Booth poverty vs 2025", fontsize=12)
ax.set_ylim(-0.2, 0.3)
style_axes(ax); ax.set_facecolor(PAPER)
ax.set_title("Move the old map 1 km and the link mostly goes", fontproperties=DISPB, fontsize=17, color=FG, loc="left")

fig.text(0.03, 0.050, f"Rank correlation {R['main_rho']['rho']:.2f} (95% CI {R['main_rho']['lo']:.2f} to {R['main_rho']['hi']:.2f}) across {R['n']['lsoa_analysis']:,} small areas (LSOAs). Holds within boroughs and north of the Thames; no clear link south of it.",
         fontsize=11.5, color=FG)
fig.text(0.03, 0.027, "Sources: Booth map, LSE Library, Charles Booth's London (Public Domain Mark), via Layers of London · streets © OpenStreetMap (ODbL)",
         fontsize=10.5, color=MUT)
fig.text(0.03, 0.015, "English Indices of Deprivation 2025 (MHCLG, OGL) · LSOA boundaries (ONS, OGL)", fontsize=10.5, color=MUT)
fig.text(0.97, 0.015, "Dr Tristan Hotham · maps.tristanhotham.com/booth-today", fontsize=11.5, color=FG, ha="right")
out = os.path.join(ROOT, "reddit", "booth_today_collage.png")
fig.savefig(out, dpi=160, facecolor=PAPER)
print(out)
