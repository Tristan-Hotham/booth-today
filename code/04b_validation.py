"""Step 4b: score the classifier against the blind by-eye labels (code/validation_test_labels.csv; the development sample code/validation_dev_labels.csv with BT_VAL). A 'mixed:a+b' label counts as
agreement if the classifier gives either colour; 'unclear' labels are reported and excluded. Writes data/validation.csv and
data/validation.json (exact agreement, within one step of the 1 to 7 scale, poor vs not poor, confusion matrix)."""
import numpy as np
import pandas as pd
from common import *

S = pd.read_csv(f"{DATA}/streets_booth.csv.gz", keep_default_na=False)
V = pd.read_csv(os.path.join(ROOT, "code", os.environ.get("BT_VAL", "validation_test_labels.csv"))).merge(
    S[["osm_id", "name", "booth", "purity", "length_m"]], on="osm_id", how="left")
assert len(V) == 200
SET = "dev" if "dev" in os.environ.get("BT_VAL", "") else "test"
V["booth"] = V.booth.replace("", "none")
V["set"] = V.label.apply(lambda s: s.split(":")[1].split("+") if s.startswith("mixed:") else ([] if s == "unclear" else [s]))
U = V[V.set.str.len() > 0].copy()
U["exact"] = [b in s for b, s in zip(U.booth, U.set)]
U["within1"] = [b != "none" and min(abs(CLASS_SCORE[b] - CLASS_SCORE[x]) for x in s) <= 1 for b, s in zip(U.booth, U.set)]
U["poor_true"] = [any(x in POOR for x in s) for s in U.set]
U["poor_pred"] = U.booth.isin(POOR)
tp = int((U.poor_true & U.poor_pred).sum()); fp = int((~U.poor_true & U.poor_pred).sum())
fn = int((U.poor_true & ~U.poor_pred).sum()); tn = int((~U.poor_true & ~U.poor_pred).sum())
single = U[~U.label.str.startswith("mixed")]
conf = pd.crosstab(pd.Categorical(single.label, CLASSES), pd.Categorical(single.booth, CLASSES), dropna=False)
pp_t = ~U.poor_true;
res = {"set": SET, "uncoloured_pred": int((U.booth == "none").sum()), "n": int(len(V)), "unclear": int((V.label == "unclear").sum()), "n_scored": int(len(U)),
       "n_mixed": int(U.label.str.startswith("mixed").sum()),
       "exact": int(U.exact.sum()), "exact_pc": round(U.exact.mean() * 100, 1),
       "within1": int(U.within1.sum()), "within1_pc": round(U.within1.mean() * 100, 1),
       "poor": {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "agree_pc": round((tp + tn) / len(U) * 100, 1),
                "sensitivity_pc": round(tp / max(tp + fn, 1) * 100, 1),
                "precision_pc": round(tp / max(tp + fp, 1) * 100, 1)},
       "poor_single": {"n_poor": int(single.label.isin(POOR).sum()),
                       "found": int((single.label.isin(POOR) & single.booth.isin(POOR)).sum()),
                       "n_notpoor": int((~single.label.isin(POOR)).sum()),
                       "false_poor": int((~single.label.isin(POOR) & single.booth.isin(POOR)).sum())},
       "by_label": {c: {"n": int((single.label == c).sum()), "correct": int(((single.label == c) & single.exact).sum())} for c in CLASSES},
       "purple_pink": {"n": int(single.label.isin(["purple", "pink"]).sum()),
                       "swapped": int(((single.label == "purple") & (single.booth == "pink")).sum() + ((single.label == "pink") & (single.booth == "purple")).sum())},
       "confusion": {r: {c: int(conf.loc[r, c]) for c in CLASSES} for r in CLASSES}}
V.drop(columns="set").to_csv(f"{DATA}/validation_{SET}.csv", index=False)
jsave(res, f"{DATA}/validation_{SET}.json", indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "confusion"}, indent=1))
print(conf)
