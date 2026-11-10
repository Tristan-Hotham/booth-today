"""Window rule shared by steps 3 and 5: from the ink fractions of a 7 x 7 window to a Booth colour (or None)."""
import numpy as np

# ink codes from 02_inks.py
NOD, PAP, GRY, BLK, DBL, LBL, OCH, RED, MAU, LRD = range(10)
CODE = ["black", "dkblue", "ltblue", "purple", "pink", "red", "yellow"]   # index 0..6; -1 = no colour; -2 = no data


def fractions(win):
    """win: (..., n) uint8 inks -> (..., 10) fractions"""
    n = win.shape[-1]
    return np.stack([(win == k).sum(-1) / n for k in range(10)], -1)


def classify(F):
    """F: (N, 10) ink fractions -> (N,) int codes into CODE, -1 uncoloured, -2 off the map"""
    blk, dbl, lbl, och, red, mau, lrd = F[:, BLK], F[:, DBL], F[:, LBL], F[:, OCH], F[:, RED], F[:, MAU], F[:, LRD]
    blue = dbl + lbl
    reds = red + mau + lrd
    out = np.full(len(F), -1, np.int8)
    col = blk + blue + och + reds
    # candidate scores; the largest wins among those passing their own floor
    s = np.full((len(F), 7), -1.0)
    s[:, 0] = np.where(blk >= 0.5, blk, -1)
    s[:, 1] = np.where((dbl >= 0.3) & (dbl >= lbl), blue, -1)
    s[:, 2] = np.where((blue >= 0.25) & (dbl < lbl + 0.0) | ((blue >= 0.25) & (dbl < 0.3)), blue, -1)
    s[:, 6] = np.where(och >= 0.25, och + 0.1, -1)
    s[:, 3] = np.where((mau >= 0.25) & (mau >= 0.5 * red), reds, -1)
    s[:, 5] = np.where((red >= 0.45) & (mau < 0.5 * red), reds, -1)
    s[:, 4] = np.where((reds >= 0.25) & (red < 0.45) & (mau < 0.5 * red + 0.25) & ~((mau >= 0.25) & (mau >= 0.5 * red)), reds, -1)
    best = s.argmax(1)
    ok = (s.max(1) > 0) & (col >= 0.3)
    out[ok] = best[ok]
    out[F[:, NOD] > 0.5] = -2
    return out


INKS7 = [BLK, DBL, LBL, OCH, RED, MAU, LRD]


def colour_mask(F):
    """window is 'coloured' if at least 30% of it is Booth colour ink, or at least half of it is solid black, and it is on the
    map. Thin black (lettering, boundary dashes, trees, outlines) does not count."""
    return ((F[:, INKS7[1:]].sum(1) >= 0.3) | (F[:, BLK] >= 0.5)) & (F[:, NOD] <= 0.5)


def pool_counts(F):
    """pixel counts of the 7 inks in a window, with black kept only where the window is solid black (>= 50%)"""
    c = F[:, INKS7] * 49
    c[:, 0] = np.where(F[:, BLK] >= 0.5, c[:, 0], 0)
    return np.round(c).astype(np.int32)


def classify_pooled(C):
    """C: (N, 7) pooled pixel counts of the seven Booth inks (black, dark blue, light blue, ochre, red, mauve, light red)
    over a street's coloured windows -> (codes into CODE, purity). Rules tuned on the development sample (see NOTES.md)."""
    C = np.asarray(C, float)
    tot = np.maximum(C.sum(1), 1e-9)
    blk, dbl, lbl, och, red, mau, lrd = (C[:, k] / tot for k in range(7))
    blue = dbl + lbl
    reds = red + mau + lrd
    rr = red / np.maximum(red + lrd, 1e-9)
    mr = mau / np.maximum(reds, 1e-9)
    out = np.where(mr >= 0.45, 3, np.where(rr >= 0.75, 5, 4))        # purple / red / pink
    pur = reds.copy()
    out = np.where(och >= 0.4, 6, out); pur = np.where(och >= 0.4, och, pur)
    isb = blue >= 0.45
    out = np.where(isb, np.where(dbl >= lbl, 1, 2), out); pur = np.where(isb, blue, pur)
    isk = blk >= 0.3
    out = np.where(isk, 0, out); pur = np.where(isk, blk, pur)
    return out.astype(np.int8), pur
