/* Booth's poverty map today. Booth's 1898-99 colours read along today's OpenStreetMap streets, and the English Indices of
 * Deprivation 2025 by LSOA, on a plain MapLibre base map (OpenFreeMap Positron). A then/now slider fades between the two;
 * the original georeferenced Booth map (LSE Library, via Layers of London / Humap) can be laid underneath.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const BOOTH_TILES = 'https://overlays.humap.site/layersoflondon/booth/{z}/{x}/{y}.png';
  const COL = ['#1E1B1B', '#1F3F8F', '#7DB0DE', '#8A4C8F', '#F0A2AE', '#CB2B32', '#EFC020'];
  const CNAME = ['Black', 'Dark blue', 'Light blue', 'Purple', 'Pink', 'Red', 'Yellow'];
  const CTEXT = ['Lowest class. Vicious, semi-criminal', 'Very poor, casual. Chronic want', 'Poor. 18s. to 21s. a week for a moderate family',
    'Mixed. Some comfortable, others poor', 'Fairly comfortable. Good ordinary earnings', 'Middle class. Well-to-do', 'Upper-middle and upper classes. Wealthy'];
  const DEC = ['#4A1426', '#6E1F35', '#8F3046', '#AD4A5B', '#C66B76', '#D88E95', '#E5AEB2', '#EECACC', '#F4E0E0', '#F1DCD8'];
  const GRP = { persistent: ['#4A1426', 'Poorest fifth on Booth\'s map, most deprived 20% today'], turned: ['#2F7FB8', 'Poorest fifth on Booth\'s map, least deprived half today'], fallen: ['#D08A1E', 'No poor street on Booth\'s map, most deprived 20% today'] };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const $ = id => document.getElementById(id);
  let map, site, mix = 0;

  $('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = $('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  $('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  $('ctFold').addEventListener('click', () => fold(true));
  $('lyrBtn').addEventListener('click', () => { const o = $('lp').classList.toggle('open'); $('lyrBtn').setAttribute('aria-expanded', o); });

  if (!window.maplibregl) { $('nojs').textContent = 'The map could not load (it needs WebGL).'; return; }
  map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-0.258, 51.447], [0.011, 51.567]], fitBoundsOptions: { padding: small ? 10 : 40 },
    minZoom: 9, maxZoom: 18, attributionControl: false, cooperativeGestures: false });
  window.__map = map;
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: 'Booth map: <a href="https://booth.lse.ac.uk/">LSE Library, Charles Booth\'s London</a> (Public Domain Mark), tiles via <a href="https://www.layersoflondon.org/">Layers of London</a> / Humap · IMD 2025: MHCLG (OGL) · LSOAs: ONS (OGL)' }), 'bottom-right');

  function setMix(v) {
    mix = v;
    const now = Math.min(1, v * 2), then = Math.min(1, (1 - v) * 2);
    if (map.getLayer('imd')) map.setPaintProperty('imd', 'fill-opacity', 0.82 * now);
    if (map.getLayer('streets')) map.setPaintProperty('streets', 'line-opacity', Math.max(0.15, then));
    $('mixTxt').textContent = v < 0.2 ? 'Booth, 1898 to 1899' : v > 0.8 ? 'Deprivation, 2025' : 'Both';
  }

  map.on('load', async () => {
    $('nojs').remove();
    document.querySelectorAll('.maplibregl-ctrl-attrib').forEach(a => a.classList.remove('maplibregl-compact-show'));
    const lbl = map.getStyle().layers.find(l => l.type === 'symbol')?.id;
    map.addSource('booth', { type: 'raster', tiles: [BOOTH_TILES], tileSize: 256, minzoom: 12, maxzoom: 16, bounds: [-0.2582, 51.4471, 0.011, 51.5669] });
    map.addLayer({ id: 'booth', type: 'raster', source: 'booth', layout: { visibility: $('lyB').checked ? 'visible' : 'none' }, paint: { 'raster-opacity': +$('opB').value } }, lbl);
    const [lsoa, streets] = await Promise.all([fetch('data/site_lsoa.geojson').then(r => r.json()), fetch('data/site_streets.geojson').then(r => r.json())]);
    map.addSource('lsoa', { type: 'geojson', data: lsoa });
    map.addLayer({ id: 'imd', type: 'fill', source: 'lsoa', paint: { 'fill-color': ['match', ['get', 'd'], ...DEC.flatMap((c, i) => [i + 1, c]), '#CCCCCC'], 'fill-opacity': 0.41 } }, lbl);
    map.addLayer({ id: 'area', type: 'line', source: 'lsoa', filter: ['==', ['get', 'a'], 1], paint: { 'line-color': '#5B4C3A', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.15, 15, 0.8], 'line-opacity': 0.45 } }, lbl);
    map.addLayer({ id: 'groups', type: 'line', source: 'lsoa', filter: ['!=', ['get', 'g'], ''], layout: { visibility: 'none' },
      paint: { 'line-color': ['match', ['get', 'g'], 'persistent', GRP.persistent[0], 'turned', GRP.turned[0], GRP.fallen[0]], 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 1.6, 15, 4] } }, lbl);
    map.addSource('streets', { type: 'geojson', data: streets });
    map.addLayer({ id: 'streets-halo', type: 'line', source: 'streets', paint: { 'line-color': '#FFFFFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 1.6, 13, 3.2, 16, 9], 'line-opacity': 0.55 } }, lbl);
    map.addLayer({ id: 'streets', type: 'line', source: 'streets', layout: { 'line-cap': 'round' },
      paint: { 'line-color': ['match', ['get', 'c'], ...COL.flatMap((c, i) => [i, c]), '#999999'], 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 1.0, 13, 2.2, 16, 6.5] } }, lbl);
    setMix(+$('mix').value);
    site = await fetch('data/site.json').then(r => r.json());
  });

  $('mix').addEventListener('input', e => setMix(+e.target.value));
  document.querySelectorAll('.chip[data-mix]').forEach(b => b.addEventListener('click', () => { $('mix').value = b.dataset.mix; setMix(+b.dataset.mix); }));
  const vis = (id, on) => map.getLayer(id) && map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
  $('lyS').addEventListener('change', e => { vis('streets', e.target.checked); vis('streets-halo', e.target.checked); });
  $('lyI').addEventListener('change', e => vis('imd', e.target.checked));
  $('lyA').addEventListener('change', e => vis('area', e.target.checked));
  $('lyG').addEventListener('change', e => { vis('groups', e.target.checked); $('keyG').hidden = !e.target.checked; });
  $('lyB').addEventListener('change', e => { vis('booth', e.target.checked); $('boothNote').hidden = !e.target.checked; if (e.target.checked && map.getZoom() < 13) map.easeTo({ zoom: 13.5 }); });
  $('opB').addEventListener('input', e => map.getLayer('booth') && map.setPaintProperty('booth', 'raster-opacity', +e.target.value));
  $('lyL').addEventListener('change', e => map.getStyle().layers.filter(l => l.type === 'symbol').forEach(l => map.setLayoutProperty(l.id, 'visibility', e.target.checked ? 'visible' : 'none')));

  map.on('click', e => {
    const f = map.queryRenderedFeatures([[e.point.x - 5, e.point.y - 5], [e.point.x + 5, e.point.y + 5]], { layers: ['streets', 'imd'].filter(l => map.getLayer(l)) });
    const st = f.find(x => x.layer.id === 'streets'), ls = f.find(x => x.layer.id === 'imd');
    if (!st && !ls) return;
    let h = '';
    if (st && mix < 0.95) {
      const p = st.properties;
      h += `<b class="t">${esc(p.n || 'Unnamed street')}</b><div class="mp"><span class="sw" style="background:${COL[p.c]}"></span>Booth: <b>${CNAME[p.c]}</b></div><div class="nt">"${CTEXT[p.c]}."</div><div class="nt">Purity ${Math.round(p.p * 100)}% (share of the coloured ink along this street in the winning colour). Read from the scanned map; check it against the original layer.</div>`;
    }
    if (ls) {
      const p = ls.properties;
      h += `${h ? '<hr>' : ''}<b class="t" style="font-size:16px">${esc(p.nm)}</b><table><tr><td>Borough</td><td>${esc(p.b)}</td></tr>${p.pl ? `<tr><td>Near</td><td>${esc(p.pl)}</td></tr>` : ''}<tr><td>IMD 2025</td><td>decile ${p.d} of 10 (score ${p.s})</td></tr>` +
        `<tr><td>Booth poor</td><td>${p.ps == null ? 'no coloured streets' : p.ps + '% of coloured street'}</td></tr><tr><td>Booth streets</td><td>${p.km} km read</td></tr></table>` +
        (p.g ? `<div class="nt" style="color:${GRP[p.g][0]}">${GRP[p.g][1]}.</div>` : '') + (p.a ? '' : '<div class="nt">Not in the analysis (under 90% on Booth\'s map or under 300 m of coloured street).</div>') +
        '<div class="nt">Decile 1 = the most deprived 10% of small areas in England.</div>';
    }
    new maplibregl.Popup({ maxWidth: '310px' }).setLngLat(e.lngLat).setHTML(h).addTo(map);
  });
  ['streets', 'imd'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });

  // search
  const q = $('q'), sug = $('sug'); let hits = [], sel = -1;
  function show() {
    const v = norm(q.value.trim()); sel = -1;
    if (!site || v.length < 2) { sug.style.display = 'none'; return; }
    hits = site.search.filter(s => norm(s[0]).includes(v)).sort((a, b) => (norm(a[0]).startsWith(v) ? 0 : 1) - (norm(b[0]).startsWith(v) ? 0 : 1) || a[0].length - b[0].length).slice(0, 12);
    sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}">${esc(h[0])} <span>${h[3] < 0 ? 'neighbourhood' : 'street, Booth ' + CNAME[h[3]].toLowerCase()}</span></li>`).join('') || '<li>No match on Booth\'s map</li>';
    sug.style.display = 'block';
  }
  function go(h) { if (!h) return; map.flyTo({ center: [h[1], h[2]], zoom: h[3] < 0 ? 14.5 : 16.2 }); sug.style.display = 'none'; q.blur(); }
  q.addEventListener('input', show);
  q.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { sel = Math.max(0, Math.min(hits.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1))); [...sug.children].forEach((li, i) => li.setAttribute('aria-selected', i === sel)); e.preventDefault(); }
    if (e.key === 'Enter') go(hits[Math.max(sel, 0)]);
    if (e.key === 'Escape') sug.style.display = 'none';
  });
  sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(hits[+li.dataset.i]); });
  document.querySelectorAll('[data-fly]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const [x, y, z] = a.dataset.fly.split(',').map(Number); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); map.flyTo({ center: [x, y], zoom: z }); }));
})();
