"""Step 11: the paper. Fills code/paper_template.tex + code/paper_body.tex from data/results.json, adds the tables and compiles
with xelatex. Output: release/paper/Hotham_Booth_Today.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder
(https://doi.org/10.5281/zenodo.24115200 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/11_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
M = jload(f"{DATA}/models.json")
V = jload(f"{DATA}/validation_test.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Booth_Today"
DOI = os.environ.get("DOI")
tx = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")

# validation table
rows = ""
for c in CLASSES:
    r = V["confusion"][c]
    rows += f"{CLASS_LABEL[c]} & " + " & ".join(str(r[k]) for k in CLASSES) + f" & {sum(r.values())}\\\\\n"
TV = ("\\begin{table}[tbp]\\centering\\small\\caption{Test sample: colour by eye (rows) against the reader (columns), ways with a single colour by eye. "
      f"Mixed ways ({V['n_mixed']}) and ways that could not be judged ({V['unclear']}) are not shown.}}\\label{{tab:valid}}"
      "\\begin{tabular}{l" + "r" * 8 + "}\\toprule By eye & Black & Dk blue & Lt blue & Purple & Pink & Red & Yellow & Total\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
# main table
f, z, se = R["main_fe"], R["main_fe_z"], R["spatial_error"]
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Main estimates. Outcome: IMD 2025 score. Exposure: Booth poverty share (black, dark blue, light blue) "
      "per 10 percentage points. (1) Spearman rank correlation, 95\\% interval from a 1~km block bootstrap (2,000 replicates). (2) OLS without and (3) with "
      "borough fixed effects, standard errors clustered by MSOA. (4) Spatial error model with borough dummies, 8 nearest neighbours.}\\label{tab:main}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrrr}\\toprule & (1) Spearman & (2) OLS & (3) OLS, borough FE & (4) Spatial error\\\\\\midrule\n"
      f"Estimate & {R['main_rho']['rho']:.3f} & {f['b_nofe']:.3f} & {f['b']:.3f} & {se['b']:.3f}\\\\\n"
      f"95\\% interval & [{R['main_rho']['lo']:.3f}, {R['main_rho']['hi']:.3f}] & [{f['lo_nofe']:.3f}, {f['hi_nofe']:.3f}] & [{f['lo']:.3f}, {f['hi']:.3f}] & [{se['lo']:.3f}, {se['hi']:.3f}]\\\\\n"
      f"Standardised outcome & & & {z['b']:.3f} [{z['lo']:.3f}, {z['hi']:.3f}] & \\\\\n"
      f"$R^2$ & & {f['r2_nofe']:.3f} & {f['r2']:.3f} & \\\\\n$\\lambda$ & & & & {se['lambda']:.3f}\\\\\n"
      f"N (LSOAs) & {R['main_rho']['n']:,} & {f['n']:,} & {f['n']:,} & {se['n']:,}\\\\\n"
      f"Clusters (MSOAs) / boroughs & & {R['n']['msoa']} & {R['n']['msoa']} / {R['n']['boroughs']} & \\\\\\bottomrule\\end{{tabular}}}}\\end{{table}}")
# crosstab
rows = ""
for q in range(1, 6):
    c = R["crosstab"][str(q)]
    rows += f"{q} & " + " & ".join(str(c[str(d)]) for d in range(1, 11)) + f" & {sum(c.values())} & {R['quintile_mean_imd'][str(q)]:.1f}\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{LSOAs by Booth poverty group (1 = no poor street; 2 to 5 = quartiles of the rest) and national IMD 2025 decile (1 = most deprived), with the mean IMD score.}\\label{tab:cross}"
      "\\begin{tabular}{l" + "r" * 12 + "}\\toprule Group & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 & 9 & 10 & N & Mean IMD\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
# robustness
rows = f"Main specification & {R['main_rho']['n']:,} & {R['main_rho']['rho']:.3f} [{R['main_rho']['lo']:.3f}, {R['main_rho']['hi']:.3f}] & {f['b']:.3f} [{f['lo']:.3f}, {f['hi']:.3f}]\\\\\n"
for r in R["robust"]:
    rows += f"{tx(r['label'])}{'' if r['planned'] else ' (not planned)'} & {r['n']:,} & {r['rho']:.3f} [{r['rho_lo']:.3f}, {r['rho_hi']:.3f}] & {r['b']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Planned robustness checks. Spearman correlation (500 block-bootstrap replicates) and within-borough OLS slope "
      "(per 10 percentage points of the exposure, or per point of the mean score; R6a in income-domain units, R6b in national rank places), 95\\% intervals.}\\label{tab:robust}"
      "\\begin{tabular}{p{6.2cm}rll}\\toprule Check & N & Spearman & Borough FE slope\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for d, lab in (("0", "None"), ("500", "500 m"), ("1000", "1 km"), ("2000", "2 km"), ("4000", "4 km")):
    s = R["shift"][d]
    rows += f"{lab} & {s['n_mean']:,} & {s['rho_mean']:.3f} & [{s['rho_min']:.3f}, {s['rho_max']:.3f}] & {s['b_mean']:.3f} & [{s['b_min']:.3f}, {s['b_max']:.3f}]\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Scale test: LSOAs shifted in eight directions; mean and range over directions of the Spearman correlation and of the within-borough slope.}\\label{tab:shift}"
      "\\begin{tabular}{lrrlrl}\\toprule Shift & Mean N & Mean rho & Range & Mean slope & Range\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

body = open(os.path.join(ROOT, "code", "paper_body.tex"), encoding="utf-8").read()
body = fill(body, R, keep=("DOI", "DOI_URL", "BLOG_URL"))
body = body.replace("%%TABLE_VALID%%", TV).replace("%%TABLE_MAIN%%", TM).replace("%%TABLE_CROSS%%", TC).replace("%%TABLE_ROBUST%%", TR).replace("%%TABLE_SHIFT%%", TS).replace("%%AI%%", AI)
doi_url = f"https://doi.org/{DOI}" if DOI else "\\{\\{DOI\\_URL\\}\\}"
body = body.replace("https://doi.org/10.5281/zenodo.24115200", doi_url)
tpl = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read().replace("%%DOIURL%%", doi_url)
tex = tpl.replace("%%BODY%%", body)
assert "{{" not in tex.replace("\\{\\{DOI\\_URL\\}\\}", ""), re.findall(r"\{\{[^}]*\}\}", tex)[:5]
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(tex)
for _ in range(2):
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
assert os.path.exists(f"{OUT}/{NAME}.pdf"), p.stdout[-2000:]
words = len(re.sub(r"\\[a-zA-Z]+|[{}$]", " ", body).split())
abstract = re.search(r"\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
print("pdf ok; words about", words, "; abstract words", len(abstract.split()))
print([l for l in p.stdout.splitlines() if "undefined" in l.lower() or "Overfull" in l][:10])
