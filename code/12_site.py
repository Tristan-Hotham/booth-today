"""Step 12: index.html from code/page_body.html, code/page_essay.html and the house CSS (code/page.css), filled from
data/results.json. 10.5281/zenodo.24115200 and https://blog.tristanhotham.com/2026/10/31/booth-today/ stay for the publisher."""
import time
from common import *

R = jload(f"{DATA}/results.json")
css = open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read()
body = open(os.path.join(ROOT, "code", "page_body.html"), encoding="utf-8").read()
essay = fill(open(os.path.join(ROOT, "code", "page_essay.html"), encoding="utf-8").read(), R)
fs = open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read()
keyrows = "".join(f'<div class="row"><span class="sw" style="background:{CLASS_HEX[c]}"></span>{CLASS_LABEL[c].lower()}: {CLASS_NAME[c].split(".")[0].lower()}</div>' for c in CLASSES)
head = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Booth's poverty map today | Are London's poorest streets of the 1890s still the poorest?</title>
<meta name="description" content="Charles Booth's 1898 to 1899 poverty colours read along every street of today's inner London and compared with the Index of Multiple Deprivation 2025. Search your street.">
<meta property="og:title" content="Booth's poverty map today">
<meta property="og:description" content="Are London's poorest streets of the 1890s still the poorest? A modest yes, and only very locally: rank correlation {R['main_rho']['rho']:.2f} across {R['n']['lsoa_analysis']:,} small areas.">
<meta property="og:image" content="{PAGE}header.png">
<meta property="og:url" content="{PAGE}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800;9..144,900&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=MedievalSharp&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css">
{css}
</head>
"""
html = head + body
for k, v in {"%%ESSAY%%": essay, "%%REPO%%": REPO, "%%BYLINE%%": BYLINE, "%%AI%%": AI, "%%FULLSCREEN%%": fs,
             "%%KEYROWS%%": keyrows, "%%NLSOA%%": f"{R['n']['lsoa_analysis']:,}", "%%VERSION%%": str(int(time.time()))}.items():
    html = html.replace(k, v)
assert "%%" not in html
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert set(re.findall(r"\{\{([^}|]+)", html)) <= {"DOI", "BLOG_URL"}, set(re.findall(r"\{\{([^}|]+)", html))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html) // 1024, "KB")
