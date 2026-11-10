"""Step 4a: the validation sample. 200 coloured street ways drawn at random (seed 2026). For each, a magnified crop of the
Booth map around the way, with the way's centreline traced as a thin cyan dotted line, is written to contact sheets in
scratch (16 per sheet) WITHOUT the classifier's answer, for labelling by eye. Labels go in code/validation_labels.csv
(sample index, osm id, label in black/dkblue/ltblue/purple/pink/red/yellow, or 'mixed:<a>+<b>' / 'unclear'), and are scored
in step 4b."""
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from common import *

S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
# development sample: seed 2026, drawn from the first version of the classifier's coloured ways (its osm ids are fixed in
# code/validation_dev_labels.csv). Test sample: seed 2027, from today's coloured ways, excluding every development way.
SET = os.environ.get("BT_SET", "test")
if SET == "dev":
    C = S[S.osm_id.isin(pd.read_csv(os.path.join(ROOT, "code", "validation_dev_labels.csv")).osm_id)]
    C = C.set_index("osm_id").loc[pd.read_csv(os.path.join(ROOT, "code", "validation_dev_labels.csv")).osm_id].reset_index()
else:
    dev = set(pd.read_csv(os.path.join(ROOT, "code", "validation_dev_labels.csv")).osm_id)
    C = S[(S.booth != "") & ~S.osm_id.isin(dev)].sample(200, random_state=2027).reset_index(drop=True)
C[["osm_id", "name", "length_m"]].assign(i=range(len(C))).to_csv(f"{SCR}/val_sample_{SET}.csv", index=False)
T = Tiles()
R, MAG = 70, 3
font = ImageFont.truetype(f"{FONTS}/IBMPlexMono-Medium.ttf", 22)


def crop(cx, cy):
    out = np.full((2 * R, 2 * R, 3), 255, np.uint8)
    for ty in range((cy - R) // 256, (cy + R) // 256 + 1):
        for tx in range((cx - R) // 256, (cx + R) // 256 + 1):
            a = T.get(tx, ty)
            if a is None:
                continue
            x0 = max(tx * 256, cx - R); x1 = min(tx * 256 + 256, cx + R); y0 = max(ty * 256, cy - R); y1 = min(ty * 256 + 256, cy + R)
            out[y0 - (cy - R):y1 - (cy - R), x0 - (cx - R):x1 - (cx - R)] = a[y0 - ty * 256:y1 - ty * 256, x0 - tx * 256:x1 - tx * 256, :3]
    return out


P = 2 * R * MAG
for s in range(0, len(C), 16):
    sheet = Image.new("RGB", (4 * (P + 10), 4 * (P + 10)), "white")
    for k, (_, r) in enumerate(C.iloc[s:s + 16].iterrows()):
        xy = np.array([[float(v) for v in p.split()] for p in r.coords.split(";")])
        X, Y = ll2px(xy[:, 0], xy[:, 1])
        cx, cy = int(ll2px(r.lon, r.lat)[0]), int(ll2px(r.lon, r.lat)[1])
        im = Image.fromarray(crop(cx, cy)).resize((P, P), Image.NEAREST)
        d = ImageDraw.Draw(im)
        pts = [((x - cx + R) * MAG, (y - cy + R) * MAG) for x, y in zip(X, Y)]
        for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
            L = max(1, int(np.hypot(x2 - x1, y2 - y1) / 6))
            for q in range(L):
                if q % 2 == 0:
                    a0, a1 = q / L, (q + 1) / L
                    d.line([(x1 + (x2 - x1) * a0, y1 + (y2 - y1) * a0), (x1 + (x2 - x1) * a1, y1 + (y2 - y1) * a1)], fill=(0, 230, 255), width=2)
        d.rectangle([0, 0, 52, 28], fill="white"); d.text((4, 2), str(s + k), font=font, fill="black")
        sheet.paste(im, ((k % 4) * (P + 10), (k // 4) * (P + 10)))
    sheet.save(f"{SCR}/val_{SET}_{s // 16:02d}.png")
print("sheets", (len(C) + 15) // 16)
