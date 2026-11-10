"""Step 2: classify every pixel of the Booth map into an "ink" and save the mosaic to scratch (never to the repo).

Ink codes: 0 no data (transparent margin), 1 paper, 2 grey base-map ink, 3 black, 4 dark blue, 5 light blue, 6 ochre (yellow),
7 bright red, 8 mauve (Booth's purple), 9 light red (pink hatching, tints). Rules are on CIELAB values (L, a, b, chroma C)
and were set by eye on the map before any deprivation data was joined.
Outputs: SCR/inks.npz (uint8 array, rows = global pixel y - Y0*256, cols = x - X0*256, plus X0, Y0) and data/ink_palette.csv
(each palette colour of the tiles with its ink)."""
import numpy as np
import pandas as pd
from PIL import Image
from skimage.color import rgb2lab
from common import *

INK = {0: "nodata", 1: "paper", 2: "grey", 3: "black", 4: "dark blue", 5: "light blue", 6: "ochre", 7: "red", 8: "mauve", 9: "light red"}


def ink_of(L, a, b):
    C = np.hypot(a, b)
    out = np.full(L.shape, 2, np.uint8)                                   # grey by default
    out[L >= 74] = 1                                                      # paper
    lr = (a >= 10) & (C >= 15) & (L >= 52); out[lr] = 9                   # light red / pink tint
    mv = (a >= 10) & (C >= 15) & (C < 38) & (L < 52); out[mv] = 8         # mauve
    rd = (a >= 10) & (C >= 38) & (b < 1.6 * a); out[rd] = 7               # bright red
    oc = (b >= 28) & (b >= 1.6 * a); out[oc] = 6                          # ochre
    bl = ((a <= -3) & (b <= 7)) | ((a <= -5) & (b <= 10))
    out[bl & (L < 45)] = 4; out[bl & (L >= 45) & (L < 74)] = 5            # blue
    out[L < 28] = 3                                                       # black
    return out


if __name__ == "__main__":
    T = Tiles(cache=4)
    ks = list(T.idx)
    X0 = min(k[0] for k in ks); Y0 = min(k[1] for k in ks)
    W = (max(k[0] for k in ks) - X0 + 1) * 256; H = (max(k[1] for k in ks) - Y0 + 1) * 256
    M = np.zeros((H, W), np.uint8)
    lut = {}
    for (x, y) in ks:
        a = T.get(x, y)
        rgb = a[..., :3].reshape(-1, 3).astype(np.int64)
        key = (rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]
        u, inv = np.unique(key, return_inverse=True)
        new = [k for k in u if k not in lut]
        if new:
            nk = np.array(new)
            c = np.stack([(nk >> 16) & 255, (nk >> 8) & 255, nk & 255], 1)[None] / 255.0
            lab = rgb2lab(c)[0]
            ik = ink_of(lab[:, 0], lab[:, 1], lab[:, 2])
            for k, v in zip(new, ik):
                lut[k] = int(v)
        ink = np.array([lut[k] for k in u], np.uint8)[inv].reshape(256, 256)
        ink[a[..., 3] < 128] = 0
        # pure white margins outside the printed sheets
        white = (a[..., 0] > 247) & (a[..., 1] > 247) & (a[..., 2] > 247)
        ink[white] = 0
        M[(y - Y0) * 256:(y - Y0 + 1) * 256, (x - X0) * 256:(x - X0 + 1) * 256] = ink
    np.savez_compressed(f"{SCR}/inks.npz", M=M, X0=X0, Y0=Y0)
    P = pd.DataFrame([(k >> 16 & 255, k >> 8 & 255, k & 255, INK[v]) for k, v in sorted(lut.items())], columns=["r", "g", "b", "ink"])
    P.to_csv(f"{DATA}/ink_palette.csv", index=False)
    cnt = np.bincount(M.ravel(), minlength=10)
    print(M.shape, len(lut), "colours;", {INK[i]: round(cnt[i] / cnt[1:].sum() * 100, 2) for i in range(1, 10)})
