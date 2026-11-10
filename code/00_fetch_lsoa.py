"""Step 0: fetch LSOA 2021 boundaries for the 33 London boroughs (E09000001 to E09000033) from drkane/geo-lookups on GitHub
(boundaries/lsoa/<LAD code>.geojson; generalised clipped boundaries from the ONS Open Geography Portal, OGL v3.0) into
scratch. They are not shipped in the release (the page ships simplified polygons of the LSOAs on the map)."""
import urllib.request
from common import *

os.makedirs(LSOA_DIR, exist_ok=True)
for i in range(1, 34):
    code = f"E09{i:06d}"
    p = f"{LSOA_DIR}/{code}.geojson"
    if not os.path.exists(p):
        urllib.request.urlretrieve(LSOA_SRC.format(code), p)
print(len(os.listdir(LSOA_DIR)), "files in", LSOA_DIR)
