# booth-today: working notes and analysis plan

"Booth's poverty map today: are London's poorest streets of the 1890s still the poorest?" Author Dr Tristan Hotham, Independent researcher.

## Status

- Phase 1 (this section and the plan below, written 2026 before any deprivation data was joined to the Booth measure): measurement of Booth's colours along modern streets; the plan for the comparison with the English Indices of Deprivation 2025.
- Phase 2: run the plan exactly as written; anything not in it is labelled exploratory.

## Sources (checked)

- Booth map tiles: Charles Booth's Descriptive Map of London Poverty, 1898-99 revision (12 sheets), LSE Library, *Charles Booth's London* (booth.lse.ac.uk). The site's About page says the original notebooks and maps are out of copyright and the digitised versions carry the Creative Commons **Public Domain Mark** ("No Known Copyright"); the site was developed by LSE Library with Humap. The georeferenced overlay is the Layers of London / Humap tile layer (overlays.humap.site/layersoflondon/booth). Decision: the raster tiles are not redistributed in the release (only our derived street classes), but the map page may show the published tile URL as a toggleable overlay credited to LSE Library and Layers of London/Humap, since the digitised maps carry the Public Domain Mark.
- Legend wording (The National Archives education page on the Whitechapel Booth map): black "Lowest class. Vicious, semi-criminal"; dark blue "Very poor, casual. Chronic want"; light blue "Poor. 18 to 21 shillings a week for a moderate family"; purple ("dark pink" on TNA) "Mixed. Some comfortable, others poor"; pink "Fairly comfortable. Good ordinary earnings"; red "Middle-class. Well-to-do"; yellow "Upper-middle and Upper classes. Wealthy". LSE: "Light blue and pink also show hatching", and combinations of colours mark mixed streets. The seven colours do not map one to one onto Booth's classes A to H.
- Streets: OpenStreetMap ways in the Booth tile box (QLever osm-planet, 2026; ODbL). 50,010 ways have their midpoint on a Booth tile (3,414 km).
- LSOA 2021 boundaries: drkane/geo-lookups (GitHub), `boundaries/lsoa/<borough code>.geojson`, built from the ONS Open Geography Portal generalised clipped boundaries (OGL v3.0). 4,994 London LSOAs.
- Deprivation: English Indices of Deprivation 2025, File 7 (MHCLG, OGL v3.0).

## Measurement (phase 1, fixed before the comparison)

- The tiles are zoom 16 Web Mercator (about 1.49 m per pixel at London's latitude) with a global palette of about 270 colours.
- Every pixel is assigned an "ink" from its CIELAB colour: paper, grey base-map ink, black, blue (dark if L < 45, light otherwise), ochre (yellow), bright red, mauve (Booth's purple prints as a dull mauve), light red. Thresholds are set by looking at the map, before any deprivation data, and are in `code/02_classify.py`.
- Booth coloured the house frontages along each street, not the roadway. Each street is sampled every 3 px along its length at 5, 7, 9 and 11 px (about 7 to 16 m) to each side of the OSM centreline, skipping 10 px at each end of the way (junctions). Each sample is a 7 x 7 px window (about 10 m). A window is "coloured" if at least 30% of it is Booth ink; its colour is the dominant ink, with blue split into dark blue (solid, mostly dark) and light blue (hatched or light), red into red (solid) and pink (hatched), mauve = purple, ochre = yellow, black = black (only if solid).
- Street segment class: the modal colour of its coloured windows, weighted equally; confidence = share of coloured windows in the modal colour; coverage = coloured windows / all windows. Segments with fewer than 4 coloured windows are "uncoloured" (parks, railways, roads Booth left blank, or streets built later over unmapped ground).
- Validation: a random sample of 200 segments with a colour (seed 2026), labelled by eye from magnified crops of the map with the street outlined, blind to the classifier's answer; report exact agreement, agreement within one step of the 1 to 7 scale, agreement on poor (black, dark blue, light blue) versus not, and the confusion matrix.

### Change to the measurement after the first validation (still before any deprivation data was joined)

- The first classifier (modal colour of 7 x 7 windows) agreed exactly with the by-eye labels for 61% of the 185 labelled ways (seed 2026 sample). Two systematic faults: narrow solid red frontages read as pink (anti-aliased edges diluted the red share of each window), and thin black lines (lettering, parish-boundary dashes, trees in parks) made streets such as The Mall and Birdcage Walk "black".
- Fixes, both fixed before any deprivation data was joined: (1) black ink counts only in windows that are at least half solid black, and a window counts as coloured only if at least 30% is colour ink or at least half is solid black; (2) each street is classified from the **pooled pixel counts** of all its coloured windows, not the mode of window classes: black if solid black is at least 30% of the colour ink; else dark or light blue if blue is at least 45% (dark if dark-blue pixels outnumber light); else yellow if ochre is at least 40%; else among the reds, purple if mauve is at least 45% of the red inks, red if bright red is at least 75% of bright plus light red, otherwise pink. The 45% and 75% cut-offs sit on a plateau of a coarse grid search on the first sample.
- Because the first sample was used to tune these rules it is now the **development sample** (`code/validation_dev_labels.csv`, 71% exact after the fixes). A fresh **test sample** of 200 coloured ways (seed 2027, excluding all development ways) was then labelled by eye, blind, and is the one reported (`code/validation_test_labels.csv`, `data/validation_test.json`).
- The labels were made by eye from the magnified crops by the analysis assistant (Claude), not by the author; the author should spot-check a subset before submission. Purple ("dark pink" in TNA's transcription) and pink are hard to tell apart in the scan, and many streets carry two colours; "mixed" labels count as a match if the classifier gives either colour.

## Analysis plan (pre-specified in a written plan; written before joining deprivation data)

**Question.** Are the parts of inner London that Booth's 1898-99 map coloured poor still the most deprived today?

**Unit.** LSOA 2021 inside the Booth map: at least 90% of its area on Booth tiles (map footprint, after removing transparent and blank margins), and at least 300 m of classified (coloured) street. Expect about 1,500 to 2,000 LSOAs.

**Exposure (main).** Booth poverty share: the street-length-weighted share of classified street in black, dark blue or light blue. Segments are split at LSOA boundaries (length within each LSOA).

**Outcome (main).** IMD 2025 score (higher = more deprived). Secondary: income domain score; IMD national rank.

**Main tests.**
1. Spearman rank correlation of Booth poverty share with IMD 2025 score, with a 95% CI from a spatial block bootstrap (resample 1 km squares of the British National Grid, 2,000 replicates). H1: rho > 0. Against H1: CI including or below 0.
2. OLS: IMD score (standardised) on Booth poverty share (0 to 1) with borough fixed effects (2024 local authority), standard errors clustered by MSOA 2021 (LSOA name without its final letter). This asks whether, within the same borough, the streets Booth coloured poor are more deprived today. Report coefficient (IMD score points per 10 percentage points of Booth poverty), CI, N, R2.
3. Moran's I (k = 8 nearest neighbours, row standardised, 999 permutations) of the Booth share, the IMD score and the model 2 residuals; if residual Moran's I is clearly positive, also fit a spatial error model (spreg ML_Error with borough dummies) as a robustness check.

**Robustness (all planned).**
- R1 exposure including purple (mixed) as poor.
- R2 exposure as the mean Booth score (1 black to 7 yellow), length-weighted.
- R3 exposure from map area rather than streets: share of all Booth-coloured pixels in the LSOA that are black, dark blue or light blue.
- R4 only segments with confidence >= 0.6.
- R5 stricter sample: 100% coverage and at least 500 m of classified street.
- R6 outcomes: income domain score; IMD rank (Spearman).
- R7 leave one borough out (range of rho and of the model 2 coefficient).
- R8 north and south of the Thames separately; City of London excluded (its tiny residential population).

**Scale / placebo test.** Shift the LSOA polygons relative to the Booth map by 500 m, 1 km, 2 km and 4 km in eight directions (re-sampling the Booth measure for shifted LSOAs, keeping those still on the map) and recompute rho and the within-borough coefficient. If persistence is a street-level, local fact, the correlation should fall as the misalignment grows; if it is only the broad east-west divide, it should barely fall. This is a falsification check on "local" persistence, not on "any" persistence.

**Descriptive (planned).**
- Share of classified street length in each colour; share poor.
- Cross-tabulation: Booth poverty quintile by IMD 2025 decile (London LSOAs in the map).
- "Persistent": Booth poverty share in the top quintile and IMD decile 1 or 2 nationally. "Turned around": top Booth quintile and IMD decile 6 to 10. "Fallen": Booth poverty share in the bottom quintile and IMD decile 1 or 2. Report counts and the boroughs and places they cluster in (named by LSOA name and by recognisable neighbourhoods only where the map shows it).

**What would count against the hypothesis.** rho near zero (CI including 0), or a within-borough coefficient near zero. A positive rho that vanishes with borough fixed effects would mean persistence only at the scale of whole boroughs.

**Interpretation limits.** Correlational and ecological. Populations have been replaced several times over; buildings, slum clearance, Blitz damage and council estates sit between the two maps; the measure is of place, not of families. IMD 2025 is a relative index of 2020s data. Booth's colours were judgements by School Board visitors and Booth's team, not measurements.

## Literature to verify (each by WebSearch/WebFetch before citing)

Orford, Dorling, Mitchell, Shaw and Davey Smith 2002 (Health and Place); Dorling, Mitchell, Shaw, Orford and Davey Smith 2000 (BMJ, "The ghost of Christmas past"); Booth 1902-03 Life and Labour; Bales 1999 or other on Booth's methods; Englander and O'Day 1995 (Retrieved riches); Gillie 1996 (Historical Journal: the origin of the poverty line); Vaughan 2018 (Mapping Society, UCL Press); Pfeffer? Lees on gentrification of London (Butler and Lees 2006; Hamnett 2003 Unequal city); Ministry of Housing IoD 2025 technical report; Noble et al. 2006 (Environment and Planning A on IMD); Moran 1950; Anselin 1988; Gregory and Ell 2007 (Historical GIS); Southall et al.; Glass 1964 (gentrification coined, London); Chetty? no. Long-run persistence: Davis and Weinstein 2002 (AER Bones, bombs); Lee and Lin 2018; Heblich, Trew and Zylberberg 2021 (JPE, East-side story); Ambrus, Field and Gonzalez 2020 (AER, Loss in the time of cholera). Each to be checked.

## Phase 2: what was run, and deviations from the plan

- Everything in the plan was run as written (`code/06_models.py`, `code/07_shift.py`), with these deviations, all reported in the paper:
  1. **Quintiles.** 579 of the 1,221 analysis LSOAs (47%) have no poor street at all, so bottom quintiles cannot be formed. Groups: 1 = no poor street; 2 to 5 = quartiles of the LSOAs with some. "Persistent" and "turned around" use the top 20% by Booth poverty share (244 LSOAs, no ties); "fallen" uses LSOAs with no poor street (not a bottom quintile).
  2. **Leave-one-borough-out** covers the 11 boroughs with at least 20 LSOAs (boroughs at the map edge have only a handful).
  3. **Exploratory, not in the plan:** the share of red and yellow street, and of yellow alone, against the IMD (labelled exploratory everywhere), and the first-version (window mode) reader as an extra robustness check.
- The residual Moran's I was clearly positive (0.28), so the planned spatial error model was fitted (spreg ML_Error with borough dummies).
- Headline: rho 0.20 (0.13 to 0.27); within-borough slope 0.69 IMD points per 10 pp (0.18 to 1.20); spatial error 0.40 (0.07 to 0.74); north of the Thames 0.25, south 0.09 (interval includes 0); shifting the map 1 km leaves rho 0.07.

## Literature: not verified in this build

The WebSearch budget for the session ran out after the Booth source pages were checked, and Crossref and publisher pages could not be fetched, so **no secondary literature is cited in the paper**. Only sources whose pages were read are cited (LSE Library Booth pages, The National Archives legend transcription, Humap case study, the data sources). Candidates to verify and add before submission (titles and details from memory, not checked):
- Orford, S., Dorling, D., Mitchell, R., Shaw, M. and Davey Smith, G. (2002) Life and death of the people of London: a historical GIS of Charles Booth's inquiry. Health and Place 8(1), 25 to 35.
- Dorling, D., Mitchell, R., Shaw, M., Orford, S. and Davey Smith, G. (2000) The ghost of Christmas past: health effects of poverty in London in 1896 and 1991. BMJ 321, 1547 to 1551.
- Booth, C. (1902 to 1903) Life and Labour of the People in London, 17 vols. Macmillan.
- Bales, K. (1999) Popular reactions to sociological research: the case of Charles Booth. Sociology 33(1).
- Englander, D. and O'Day, R. (eds) (1995) Retrieved Riches: Social Investigation in Britain 1840 to 1914. Scolar Press.
- Vaughan, L. (2018) Mapping Society: The Spatial Dimensions of Social Cartography. UCL Press (open access).
- Gregory, I. N. and Ell, P. S. (2007) Historical GIS. Cambridge University Press.
- Glass, R. (1964) London: Aspects of Change. MacGibbon and Kee.
- Hamnett, C. (2003) Unequal City: London in the Global Arena. Routledge.
- Butler, T. and Lees, L. (2006) Super-gentrification in Barnsbury, London. Transactions of the IBG 31(4).
- Heblich, S., Trew, A. and Zylberberg, Y. (2021) East-side story: historical pollution and persistent neighborhood sorting. Journal of Political Economy 129(5).
- Davis, D. and Weinstein, D. (2002) Bones, bombs, and break points. American Economic Review 92(5).
- Ambrus, A., Field, E. and Gonzalez, R. (2020) Loss in the time of cholera. American Economic Review 110(2).
- Lee, S. and Lin, J. (2018) Natural amenities, neighbourhood dynamics, and persistence in the spatial distribution of income. Review of Economic Studies 85(1).
- Noble, M., Wright, G., Smith, G. and Dibben, C. (2006) Measuring multiple deprivation at the small-area level. Environment and Planning A 38(1).
- Moran, P. A. P. (1950) Notes on continuous stochastic phenomena. Biometrika 37.
- Anselin, L. (1988) Spatial Econometrics: Methods and Models. Kluwer.
- MHCLG (2025) English Indices of Deprivation 2025: technical report.

## Validation labels

Both samples were labelled by eye by the analysis assistant (Claude) from magnified crops, blind to the classifier, not by the author. An independent human spot-check of the test labels (`code/validation_test_labels.csv`, sheets regenerated by `BT_SET=test python3 code/04_validation_sheets.py`) is recommended before journal submission.

## Literature: verified in review (2026)

Checked online (publisher, repository or author pages) and now cited in the paper, blog and README: Dorling et al. 2000 (BMJ 321(7276), 1547 to 1551, doi 10.1136/bmj.321.7276.1547; 132 wards, Booth index vs 1991 census poverty r = 0.73); Orford et al. 2002 (Health and Place 8(1), 25 to 35, doi 10.1016/S1353-8292(01)00033-8); Vaughan 2018 (Mapping Society, UCL Press, doi 10.14324/111.9781787353053); Vaughan, Clark and Sahbaz 2005 (Space Syntax Symposium, Delft); Low 2019 (UCL CASA MSc dissertation, unpublished; hand-vectorised 8 of 12 sheets, MSOA, council tax bands, spatial lag); Heblich, Trew and Zylberberg 2021 (JPE 129(5), 1508 to 1552, doi 10.1086/713101). Gregory and Ell 2007 (Historical GIS, CUP, ISBN 978-0-521-85563-1) exists but was not read, so it is not cited. The rest of the list above is still unverified.
