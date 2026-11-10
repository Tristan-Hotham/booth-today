"""Step 14: README.md, LICENSE and reddit/post.md, every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
r = lambda p, f=None: fmt(get(R, p), f)
readme = f"""# Booth's poverty map today

Are London's poorest streets of the 1890s still the poorest? Charles Booth's 1898 to 1899 poverty colours, read by machine along every street of today's inner London, compared with the English Index of Multiple Deprivation 2025 for {r('n.lsoa_analysis', 'int')} small areas.

Interactive page: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.24115200}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/booth-today/}}
Code and data: {REPO}

## Headline results

- Booth colours read along {r('streets.ways_classified', 'int')} OpenStreetMap street pieces ({r('streets.km_classified', 'int')} km). {r('streets.poor_pc', 'f1')}% of the classified length is black, dark blue or light blue; {r('streets.share.purple', 'f1')}% purple.
- Validation on a fresh blind sample of 200 coloured ways: exact agreement {r('validation.test.exact_pc', 'f1')}% of the {r('validation.test.n_scored', 'int')} judgeable ways, within one step {r('validation.test.within1_pc', 'f1')}%; no comfortable street read as poor, but only {r('validation.test.poor.sensitivity_pc', 'f1')}% of streets with any poor colour detected.
- Rank correlation of the Booth poverty share with the IMD 2025 score: {r('main_rho.rho', 'f2')} (95% CI {r('main_rho.lo', 'f2')} to {r('main_rho.hi', 'f2')}; N = {r('main_rho.n', 'int')}).
- Within boroughs: +{r('main_fe.b', 'f2')} IMD points per 10 percentage points of Booth poverty (95% CI {r('main_fe.lo', 'f2')} to {r('main_fe.hi', 'f2')}); spatial error model {r('spatial_error.b', 'f2')} ({r('spatial_error.lo', 'f2')} to {r('spatial_error.hi', 'f2')}).
- Booth's full 1 to 7 score: rho {r('mean_score.rho', 'f2')}. Purple counted as poor: {r('purple.rho', 'f2')}. Exploratory: share of red and yellow street, {r('exploratory.rich_share.rho.rho', 'f2')}.
- North of the Thames rho {r('thames.north.rho', 'f2')}; south {r('thames.south.rho', 'f2')} (CI {r('thames.south.rho_lo', 'f2')} to {r('thames.south.rho_hi', 'f2')}).
- Scale: shifting the old map by 500 m, 1 km and 2 km gives mean rho {r('shift.500.rho_mean', 'f2')}, {r('shift.1000.rho_mean', 'f2')} and {r('shift.2000.rho_mean', 'f2')}.
- {r('groups.persistent.n', 'int')} small areas in the poorest Booth fifth are in England's most deprived fifth today; {r('groups.turned.n', 'int')} are in the less deprived half; {r('groups.fallen.n', 'int')} areas with no poor street on Booth's map are now in the most deprived fifth.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js`, `img/` | Interactive page: MapLibre on OpenFreeMap Positron; Booth colours along today's streets and IMD 2025 deciles by LSOA, a then/now slider, the original Booth map as a layer, on by default from zoom 12 (loaded from Layers of London, not stored here), search, full screen. |
| `header.png` | Social card, 1200 x 630. |
| `data/streets.csv.gz` | OpenStreetMap ways on the Booth map (ODbL). |
| `data/streets_booth.csv.gz` | Each way with pooled ink counts, Booth colour, purity and the first-version colour (ODbL). |
| `data/ink_palette.csv` | Every colour in the tiles and the ink it was assigned. |
| `data/lsoa_booth.csv`, `data/lsoa_analysis.csv` | Booth measures and IMD 2025 for every London LSOA; the analysis sample with groups and neighbourhood names. |
| `data/validation_*.csv/json`, `code/validation_*_labels.csv` | Development and test validation samples, labels and scores. |
| `data/models.json`, `data/shift.json`, `data/results.json` | Every estimate; every number quoted anywhere. |
| `data/site_*.geojson`, `data/site.json`, `data/lsoa_london.geojson` | Page data. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the deprivation data were joined. |

## Method in brief

- Every pixel of the georeferenced Booth tiles (zoom 16, about 1.5 m) is sorted into paper, base-map grey or one of Booth's inks by its CIELAB colour.
- Each OpenStreetMap way is sampled every 4.5 m, 7 to 16 m either side of its centreline (Booth coloured the frontages); ink is pooled over the coloured windows and the way gets the dominant colour.
- Validation: a development sample (used to fix the rules) and a fresh blind test sample of 200 ways each, labelled by eye from magnified crops. The labels were made by an AI model (Claude), not by a person; an independent human check is still to do.
- Ways are split at LSOA 2021 boundaries; each LSOA (at least 90% on the map, at least 300 m of coloured street) gets the share of its coloured street length in black, dark blue or light blue.
- Tests, pre-specified in a written plan: Spearman correlation with a 1 km block bootstrap; OLS with borough fixed effects, errors clustered by MSOA; Moran's I and a spatial error model; planned robustness checks; a scale test that shifts the polygons by up to 4 km.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, scikit-image, shapely, pyproj, rasterio, statsmodels, libpysal, spreg, matplotlib, Pillow; xelatex; node with Playwright for QA. Raw inputs are listed in `code/common.py` (the Booth tiles are not included; they are LSE Library's, served by Layers of London).

```
python3 code/00_fetch_lsoa.py         # LSOA 2021 boundaries from GitHub (scratch)
python3 code/01_roads.py              # OSM ways on the map
python3 code/02_inks.py               # ink of every pixel (scratch)
python3 code/03_streets.py            # Booth colour of every way
python3 code/04_validation_sheets.py  # blind contact sheets (BT_SET=dev or test)
python3 code/04b_validation.py        # scores (BT_VAL=validation_dev_labels.csv for the development sample)
python3 code/05_lsoa.py               # LSOA measures
python3 code/06_models.py             # the planned analysis
python3 code/07_shift.py              # scale test (slow)
python3 code/08_results.py            # results.json
python3 code/09_figures.py            # figures and header
python3 code/10_site_data.py          # page data
python3 code/11_paper.py              # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/12_site.py               # index.html
python3 reddit/collage.py
python3 code/14_readme.py             # README, LICENSE, Reddit post
python3 code/13_release.py            # blog post, Zenodo files
```

## Related work

- Dorling, Mitchell, Shaw, Orford and Davey Smith (2000, BMJ 321, 1547 to 1551, https://doi.org/10.1136/bmj.321.7276.1547) matched Booth's survey to 132 inner London wards of 1991: Booth's poverty index correlated at 0.73 with a 1991 census poverty index, and some causes of death in 1991 to 1995 were better predicted by 1896 poverty. Orford et al. (2002, Health and Place 8(1), 25 to 35, https://doi.org/10.1016/S1353-8292(01)00033-8) describe the historical GIS behind it.
- Vaughan (2018) Mapping Society (UCL Press, open access, https://doi.org/10.14324/111.9781787353053) on Booth's maps and social cartography; Heblich, Trew and Zylberberg (2021, Journal of Political Economy 129(5), https://doi.org/10.1086/713101) on persistent east-side deprivation in English cities. This study differs in reading the whole map automatically along streets, using small areas (LSOAs), and testing the spatial scale of persistence.

## Sources and licences

- Booth's map: Descriptive Map of London Poverty 1898 to 1899, LSE Library, Charles Booth's London (https://booth.lse.ac.uk/); the digitised maps carry the Creative Commons Public Domain Mark. Georeferenced tiles via Layers of London / Humap. Reproduced for non-commercial research; the tiles are not redistributed here.
- Legend wording as transcribed by The National Archives (Archives Live: Whitechapel).
- Streets: OpenStreetMap contributors (ODbL), via QLever.
- English Indices of Deprivation 2025, File 7 (MHCLG, Open Government Licence v3.0).
- LSOA 2021 boundaries: ONS Open Geography Portal (OGL v3.0), via drkane/geo-lookups on GitHub. Neighbourhood names: Wikidata (CC0).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and derived data CC BY 4.0, except the street files derived from OpenStreetMap (ODbL); code MIT.

## Citation

Hotham, T. (2026) Booth's poverty map today: street-level persistence of poverty in inner London, 1898 to 2025. Zenodo. https://doi.org/{{10.5281/zenodo.24115200}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data: Creative Commons Attribution 4.0 International (CC BY 4.0), except data/streets.csv.gz,
data/streets_booth.csv.gz and data/site_streets.geojson, which are derived from OpenStreetMap and shared under the Open Database Licence
(ODbL 1.0). Booth's map: LSE Library, Charles Booth's London (Public Domain Mark); not included.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""# [OC] Booth's 1899 poverty map vs deprivation today: London's poor streets of the 1890s are still slightly poorer (rank correlation {r('main_rho.rho', 'f2')}), but only street by street

Charles Booth's investigators coloured every street of inner London in 1898 to 1899, black and blue for the poor up to yellow for the wealthy. I read those colours by machine along {r('streets.km_classified', 'int')} km of today's streets and compared them with the 2025 Index of Multiple Deprivation for {r('n.lsoa_analysis', 'int')} small areas.

- Areas with more black and blue streets in 1899 are a bit more deprived today: rank correlation {r('main_rho.rho', 'f2')} (95% CI {r('main_rho.lo', 'f2')} to {r('main_rho.hi', 'f2')}).
- The wealthy end lasts better (an exploratory check, added after the main result): areas with lots of red and yellow streets are clearly less deprived now ({r('exploratory.rich_share.rho.rho', 'f2')}).
- It is very local: slide the old map 1 km and the correlation falls to {r('shift.1000.rho_mean', 'f2')}.
- North of the Thames it holds; south of it there is no clear link.

Interactive map (search your street): {PAGE}

**Source comment:** Booth map: LSE Library, Charles Booth's London (Public Domain Mark), georeferenced tiles via Layers of London. Streets: OpenStreetMap (ODbL). Deprivation: English Indices of Deprivation 2025 (MHCLG, OGL). LSOA boundaries: ONS (OGL). Tools: Python (numpy, scikit-image, statsmodels, spreg, matplotlib), MapLibre. Colour reading checked by eye on 200 random streets (labels by an AI model, Claude, from magnified crops): {r('validation.test.exact_pc', 'f0')}% exact, {r('validation.test.within1_pc', 'f0')}% within one step.
"""
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS", "civil serv", "pre-registered"):
        assert bad not in t, bad
print("README, LICENSE, post.md written")
