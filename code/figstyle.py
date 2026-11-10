"""House style for the static figures: light paper, Fraunces titles, Source Serif and IBM Plex Mono text; Booth's seven colours
from common.CLASS_HEX and a single-hue sequence for the IMD 2025 deciles."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from common import *

_FD = os.path.join(SCR, "fonts")
os.makedirs(_FD, exist_ok=True)
if not os.path.exists(f"{_FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{_FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{_FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{_FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72", "axes.unicode_minus": False, "pdf.fonttype": 42})
PAPER, FG, MUT, RULE = "#F6F4EF", "#1D2128", "#636A72", "#DDD8CC"
EDGE = "#B9AE98"
HOT = "#B3202A"
# IMD 2025 national deciles, 1 = most deprived: one hue, dark = deprived
DEC = ["#4A1426", "#6E1F35", "#8F3046", "#AD4A5B", "#C66B76", "#D88E95", "#E5AEB2", "#EECACC", "#F4E0E0", "#F1DCD8"]


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)


def savefig(fig, stem, blog=None, img=None, pdf=True):
    """f_<stem>.pdf for the paper, release/blog/b_<blog>.png at 1800 px wide, img/<img>.jpg for the page"""
    os.makedirs(f"{REL}/paper", exist_ok=True); os.makedirs(f"{REL}/blog", exist_ok=True)
    if pdf:
        fig.savefig(f"{REL}/paper/f_{stem}.pdf", facecolor=fig.get_facecolor())
    w = fig.get_figwidth()
    if blog:
        fig.savefig(f"{REL}/blog/b_{blog}.png", dpi=1800 / w, facecolor=fig.get_facecolor())
    if img:
        tmp = f"{SCR}/_tmp.png"
        fig.savefig(tmp, dpi=1400 / w, facecolor=fig.get_facecolor())
        from PIL import Image
        Image.open(tmp).convert("RGB").save(f"{IMG}/{img}.jpg", quality=86, optimize=True)
        os.remove(tmp)
    plt.close(fig)
