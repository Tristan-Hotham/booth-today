"""Step 13: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo). 10.5281/zenodo.24115200, https://doi.org/10.5281/zenodo.24115200 and https://blog.tristanhotham.com/2026/10/31/booth-today/
are left for the publisher to fill. The Booth map tiles are never included."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Booth_Today"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Booth's poverty map today",
        "slug": "booth-today",
        "excerpt": f"I read Charles Booth's 1898 to 1899 poverty colours along every street of today's inner London and set them against deprivation in 2025. The poorer streets of the 1890s are still slightly more deprived (rank correlation {R['main_rho']['rho']:.2f}), and only very locally: slide the old map 1 km and most of the link goes.",
        "seo_description": f"Are London's poorest streets of the 1890s still the poorest? Booth's poverty map read street by street against deprivation in 2025.",
        "tags": ["maps", "data visualisation", "London", "Charles Booth", "poverty", "deprivation", "history", "historical GIS"],
        "header_alt": "Title card on pale paper reading 'Booth's poverty map today' beside a map of central London streets drawn in Booth's colours: yellow in the West End, reds and pinks across the city, blues and purples in the east."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("streets_booth.csv.gz", "lsoa_booth.csv", "lsoa_analysis.csv", "ink_palette.csv", "validation_dev.csv", "validation_test.csv",
               "validation_dev.json", "validation_test.json", "models.json", "shift.json", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = (ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("~", " ")
      .replace("\\textit{", "").replace("}", "").replace("--", " to "))
zmeta = {"title": "Booth's Poverty Map Today: Street-Level Persistence of Poverty in Inner London, 1898 to 2025",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/booth-today/}}.</p>"
                        "<p>Sources: Charles Booth's Descriptive Map of London Poverty 1898 to 1899, LSE Library, Charles Booth's London (digitised maps under the "
                        "Public Domain Mark), georeferenced tiles via Layers of London / Humap (not redistributed here); OpenStreetMap (ODbL); English Indices of "
                        "Deprivation 2025 (MHCLG, Open Government Licence v3.0); LSOA 2021 boundaries (ONS, OGL v3.0) via drkane/geo-lookups; Wikidata (CC0). "
                        "Text, figures and derived data CC BY 4.0, except the street classification derived from OpenStreetMap, shared under the ODbL; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Charles Booth", "poverty", "London", "historical GIS", "persistence", "Index of Multiple Deprivation", "map digitisation", "urban history"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
