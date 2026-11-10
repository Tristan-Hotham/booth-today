# [OC] Booth's 1899 poverty map vs deprivation today: London's poor streets of the 1890s are still slightly poorer (rank correlation 0.20), but only street by street

Charles Booth's investigators coloured every street of inner London in 1898 to 1899, black and blue for the poor up to yellow for the wealthy. I read those colours by machine along 2,380 km of today's streets and compared them with the 2025 Index of Multiple Deprivation for 1,221 small areas.

- Areas with more black and blue streets in 1899 are a bit more deprived today: rank correlation 0.20 (95% CI 0.13 to 0.27).
- The wealthy end lasts better (an exploratory check, added after the main result): areas with lots of red and yellow streets are clearly less deprived now (-0.36).
- It is very local: slide the old map 1 km and the correlation falls to 0.07.
- North of the Thames it holds; south of it there is no clear link.

Interactive map (search your street): https://maps.tristanhotham.com/booth-today/

**Source comment:** Booth map: LSE Library, Charles Booth's London (Public Domain Mark), georeferenced tiles via Layers of London. Streets: OpenStreetMap (ODbL). Deprivation: English Indices of Deprivation 2025 (MHCLG, OGL). LSOA boundaries: ONS (OGL). Tools: Python (numpy, scikit-image, statsmodels, spreg, matplotlib), MapLibre. Colour reading checked by eye on 200 random streets (labels by an AI model, Claude, from magnified crops): 73% exact, 93% within one step.
