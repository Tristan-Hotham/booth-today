"""Shared paths, constants and helpers for booth-today ("Booth's poverty map today").

Inputs (read in place, never copied into the study):
  BOOTH/booth_z16_pack{0..19}.bin + booth_z16_index.json
        Raster tiles of Charles Booth's Descriptive Map of London Poverty 1898-99 (LSE Library, Charles Booth's London,
        booth.lse.ac.uk; digitised maps released under the Creative Commons Public Domain Mark), as georeferenced and served
        by Humap for LSE Library / Layers of London (overlays.humap.site/layersoflondon/booth). Web Mercator zoom 16, 256 px
        PNG tiles; index [x, y, pack, byte offset, length]. The tiles are NOT redistributed in this study: only the street
        classification derived from them.
  BOOTH/london_osm_roads.tsv
        84,013 OpenStreetMap ways inside Greater London within the Booth tile box (?w way URI, ?name, ?hw highway, ?wkt
        LINESTRING), via QLever osm-planet, 2026. OpenStreetMap contributors, ODbL.
  DEPRIV/IoD2025_File7_all_ranks_scores_deciles.csv
        English Indices of Deprivation 2025, File 7, LSOA 2021 (MHCLG, Open Government Licence v3.0).
  LSOA_DIR/E090000NN.geojson
        LSOA 2021 boundaries (generalised clipped, ONS Open Geography Portal, OGL v3.0) for the 33 London boroughs, from
        drkane/geo-lookups on GitHub (boundaries/lsoa/<LAD code>.geojson), fetched into scratch by 00_fetch_lsoa.py.
"""
import io, json, os, re, math, gzip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOTH = os.environ.get("BT_BOOTH", "/home/claude/newdata/raw_new14/booth")
DEPRIV = os.environ.get("BT_DEPRIV", "/home/claude/newdata/raw_new14/deprivation/IoD2025_File7_all_ranks_scores_deciles.csv")
SCR = os.environ.get("BT_SCRATCH", "/home/claude/scratch/booth-today")
LSOA_DIR = os.path.join(SCR, "lsoa")
LSOA_SRC = "https://raw.githubusercontent.com/drkane/geo-lookups/main/boundaries/lsoa/{}.geojson"
FONTS = os.environ.get("BT_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "booth-today"
TITLE = "Booth's poverty map today"
SUBTITLE = "Are London's poorest streets of the 1890s still the poorest?"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
TILE_URL = "https://overlays.humap.site/layersoflondon/booth/{z}/{x}/{y}.png"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
Z = 16

# Booth's seven map colours, poorest to wealthiest, with the legend wording of the 1898-99 map (as transcribed by The
# National Archives education service). The colours are not his classes A to H; light blue covers his poor classes C and D.
CLASSES = ["black", "dkblue", "ltblue", "purple", "pink", "red", "yellow"]
CLASS_NAME = {
    "black": "Lowest class. Vicious, semi-criminal",
    "dkblue": "Very poor, casual. Chronic want",
    "ltblue": "Poor. 18s. to 21s. a week for a moderate family",
    "purple": "Mixed. Some comfortable, others poor",
    "pink": "Fairly comfortable. Good ordinary earnings",
    "red": "Middle class. Well-to-do",
    "yellow": "Upper-middle and upper classes. Wealthy",
}
CLASS_LABEL = {"black": "Black", "dkblue": "Dark blue", "ltblue": "Light blue", "purple": "Purple", "pink": "Pink",
               "red": "Red", "yellow": "Yellow"}
# display colours for our own maps and figures (chosen to echo the printed map, not sampled from it)
CLASS_HEX = {"black": "#1E1B1B", "dkblue": "#1F3F8F", "ltblue": "#7DB0DE", "purple": "#8A4C8F", "pink": "#F0A2AE",
             "red": "#CB2B32", "yellow": "#EFC020"}
CLASS_SCORE = {c: i + 1 for i, c in enumerate(CLASSES)}   # 1 = black ... 7 = yellow
POOR = {"black", "dkblue", "ltblue"}            # the three colours of poverty (pre-specified)
POOR_P = {"black", "dkblue", "ltblue", "purple"}  # sensitivity: with the mixed colour


def px2ll(X, Y, z=Z):
    import numpy as np
    n = 256 * 2 ** z
    lon = np.asarray(X, float) / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * np.asarray(Y, float) / n))))
    return lon, lat


def ll2px(lon, lat, z=Z):
    import numpy as np
    n = 256 * 2 ** z
    lat = np.radians(np.asarray(lat, float))
    return (np.asarray(lon, float) + 180.0) / 360.0 * n, (1 - np.log(np.tan(lat) + 1 / np.cos(lat)) / np.pi) / 2 * n


class Tiles:
    """Random access to the packed Booth tiles; decoded tiles cached as RGBA uint8 arrays."""

    def __init__(self, cache=600):
        ix = json.load(open(os.path.join(BOOTH, "booth_z16_index.json")))
        self.idx = {(t[0], t[1]): (t[2], t[3], t[4]) for t in ix["idx"]}
        self.f = {}
        self.cache = {}
        self.order = []
        self.max = cache

    def raw(self, x, y):
        p, o, n = self.idx[(x, y)]
        if p not in self.f:
            self.f[p] = open(os.path.join(BOOTH, f"booth_z16_pack{p}.bin"), "rb")
        fh = self.f[p]; fh.seek(o)
        return fh.read(n)

    def get(self, x, y):
        import numpy as np
        from PIL import Image
        k = (x, y)
        if k in self.cache:
            return self.cache[k]
        if k not in self.idx:
            a = None
        else:
            a = np.asarray(Image.open(io.BytesIO(self.raw(x, y))).convert("RGBA"))
        self.cache[k] = a; self.order.append(k)
        if len(self.order) > self.max:
            old = self.order.pop(0); self.cache.pop(old, None)
        return a


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    if f == "abs2": return f"{abs(float(v)):.2f}"
    raise ValueError(f)


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE")
                  else fmt(get(R, m.group(1)), m.group(3)), t)
