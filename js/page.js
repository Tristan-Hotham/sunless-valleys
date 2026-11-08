/* Britain's sunless valleys: the map (The Inked World with the terrain-shadow layers and every settlement) and the
 * horizon panel (the skyline seen from a place, with the winter sun's path drawn over it).
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const BASE = window.INKBASE;
  const V = '?v=20261108';
  const ENGINE = ['js/curated.js', 'js/ink-palette.js', 'js/ink-icons.js', 'js/ink-houses.js', 'js/ink-map.js', 'js/ink-extras.js'];
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const BOUNDS = [[-10.8, 49.8], [2.0, 61.0]];
  const START = small ? [[-6.6, 50.0], [1.8, 58.7]] : [[-11, 49.9], [2.2, 59.2]];
  const RASTERS = { lost: 'Sun blocked by hills', hours: 'Hours of direct sun', dark: 'Days with no direct sun' };
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  let map = null, PL = null, byId = {}, curRaster = qs.get('layer') in RASTERS ? qs.get('layer') : 'lost';
  const profCache = {};

  // page theme (the map stays parchment)
  document.getElementById('theme').addEventListener('click', () => {
    const r = document.documentElement, dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    r.dataset.theme = dark ? 'light' : 'dark';
  });
  const ct = document.getElementById('cartouche');
  const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function loadScripts(list) {
    return list.reduce((p, src) => p.then(() => new Promise((res, rej) => {
      const el = document.createElement('script'); el.src = BASE + src + V; el.onload = res; el.onerror = () => rej(new Error('script ' + src)); document.head.appendChild(el);
    })), Promise.resolve());
  }
  const hm = m => { m = Math.round(m); const h = Math.floor(m / 60), r = m % 60; return h ? `${h} h ${String(r).padStart(2, '0')} min` : `${r} min`; };
  function dayLabel(offset) {           // offset in days from 21 December
    const d = new Date(Date.UTC(2026, 11, 21 + offset));
    return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
  }
  function darkSpan(nd) {
    if (!nd) return '';
    if (nd >= 181) return 'at least 181 days, from before 22 Sep to after 20 Mar';
    const k = (nd - 1) / 2;
    return `${nd} days, about ${dayLabel(-k)} to ${dayLabel(k)}`;
  }

  // ---------------- the sun (the same formulas as code/02_horizon.py)
  const rad = Math.PI / 180;
  function decl(k) { return -23.44 * Math.cos(rad * 360 / 365 * (355 - k + 10)); }
  function refr(h) { h = Math.max(h, -1.5); return 1.02 / Math.tan(rad * (h + 10.3 / (h + 5.11))) / 60; }
  function altAt(lat, dec, az) {
    const a = Math.sin(lat * rad), b = Math.cos(lat * rad) * Math.cos(az * rad), r = Math.hypot(a, b), psi = Math.atan2(b, a);
    const h = (Math.asin(Math.max(-1, Math.min(1, Math.sin(dec * rad) / r))) - psi) / rad;
    return h + refr(h);
  }

  // ---------------- the horizon panel
  const hz = document.getElementById('hz');
  document.getElementById('hzClose').addEventListener('click', () => { hz.hidden = true; });
  function profile(p) {
    const key = `${(Math.floor(p.lat * 2) / 2).toFixed(1)}_${Math.floor(p.lon)}`;
    if (!profCache[key]) profCache[key] = fetch(`data/prof/${key}.json`).then(r => r.json());
    return profCache[key].then(j => {
      const b = atob(j[p.qid] || ''); const out = [];
      for (let i = 0; i < b.length; i++) out.push(b.charCodeAt(i) / 4 - 2);
      return out;                                  // azimuth 60, 62, ... 300
    });
  }
  function drawPanel(p, hor) {
    const W = 560, H = 230, ml = 34, mr = 10, mt = 12, mb = 26;
    const top = Math.max(20, Math.ceil((Math.max(...hor, altAt(p.lat, -23.44, 180)) + 4) / 5) * 5);
    const X = az => ml + (az - 60) / 240 * (W - ml - mr), Y = a => mt + (1 - (a + 2) / (top + 2)) * (H - mt - mb);
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Skyline and winter sun path seen from ${esc(p.name)}">`;
    s += `<rect x="${ml}" y="${mt}" width="${W - ml - mr}" height="${H - mt - mb}" fill="#FBF5E4"/>`;
    for (let a = 0; a <= top; a += 5) s += `<line x1="${ml}" x2="${W - mr}" y1="${Y(a)}" y2="${Y(a)}" stroke="#E2D3AE" stroke-width="${a ? 0.6 : 1.2}"/><text x="${ml - 4}" y="${Y(a) + 3.5}" text-anchor="end" class="ax">${a}°</text>`;
    [[90, 'E'], [135, 'SE'], [180, 'S'], [225, 'SW'], [270, 'W']].forEach(([az, l]) => { s += `<line x1="${X(az)}" x2="${X(az)}" y1="${mt}" y2="${H - mb}" stroke="#E2D3AE" stroke-width="0.6"/><text x="${X(az)}" y="${H - 9}" text-anchor="middle" class="ax">${l}</text>`; });
    // sun paths: 21 Dec, about 21 Nov and 21 Jan, about 21 Oct and 21 Feb
    const paths = [[0, '#A3261B', '21 Dec'], [31, '#C77A2A', '21 Nov, 21 Jan'], [61, '#B8862B', '21 Oct, 21 Feb']];
    paths.slice().reverse().forEach(([k, col, lab], i) => {
      const dec = decl(k); let d = '', lit = '', prev = false;
      for (let az = 60; az <= 300; az += 1) {
        const a = altAt(p.lat, dec, az); if (a < -1.5) { prev = false; continue; }
        const hi = Math.max(0, hor[Math.min(120, Math.round((az - 60) / 2))]);
        d += `${d && prev ? 'L' : 'M'}${X(az).toFixed(1)},${Y(a).toFixed(1)}`; prev = true;
      }
      s += `<path d="${d}" fill="none" stroke="${col}" stroke-width="${k ? 1.3 : 2.2}" stroke-dasharray="${k ? '4 3' : ''}"/>`;
    });
    // the skyline, filled
    let poly = `M${X(60)},${Y(-2)}`;
    hor.forEach((v, i) => { poly += `L${X(60 + 2 * i).toFixed(1)},${Y(Math.max(-2, v)).toFixed(1)}`; });
    poly += `L${X(300)},${Y(-2)}Z`;
    s += `<path d="${poly}" fill="#2B2119" fill-opacity="0.82" stroke="#2B2119" stroke-width="1"/>`;
    // where the solstice sun clears the skyline
    let seg = '', on = false;
    for (let az = 60; az <= 300; az += 0.5) {
      const a = altAt(p.lat, -23.44, az), hv = hor[Math.min(120, Math.round((az - 60) / 2))];
      const vis = a > Math.max(0, hv);
      if (vis) { seg += `${on ? 'L' : 'M'}${X(az).toFixed(1)},${Y(a).toFixed(1)}`; }
      on = vis;
    }
    if (seg) s += `<path d="${seg}" fill="none" stroke="#F0B23A" stroke-width="5" stroke-linecap="round" opacity="0.95"/>`;
    s += `<text x="${W - mr - 4}" y="${mt + 13}" text-anchor="end" class="lg"><tspan fill="#A3261B">━ 21 Dec</tspan>  <tspan fill="#C77A2A">╍ 21 Nov, 21 Jan</tspan>  <tspan fill="#B8862B">╍ 21 Oct, 21 Feb</tspan>  <tspan fill="#D99A1E">━ direct sun</tspan></text>`;
    s += '</svg>';
    return s;
  }
  function openPanel(p) {
    hz.hidden = false;
    const lost = p.flat - p.sol;
    document.getElementById('hzTitle').textContent = p.name;
    const disputed = p.osm && p.sol === 0 && p.osm[1] > 0;
    document.getElementById('hzText').innerHTML = (disputed
      ? `<b>Uncertain: depends on the point.</b> At its Wikidata point (drawn here) the hills hide the sun on 21 December, but at its OpenStreetMap point ${p.osm[0].toFixed(1)} km away it gets ${hm(p.osm[1])} of direct sun, so this is not counted as a sunless place.`
      : (p.sol === 0
      ? `<b>No direct sun on 21 December.</b> `
      : `<b>${hm(p.sol)}</b> of direct sun on 21 December, out of ${hm(p.flat)} with a flat horizon (${Math.round(100 * lost / p.flat)}% lost). `)
      + (p.nod ? `No direct sun for ${darkSpan(p.nod)}.` : '')
      + (p.osm && p.sol === 0 ? ` Also sunless at its OpenStreetMap point ${p.osm[0].toFixed(1)} km away.` : ''))
      + `<br><span class="nt">${esc(p.county)}${p.nation >= 0 ? ', ' + esc(PL.nations[p.nation]) : ''} · ${p.elev} m${p.pop ? ' · population ' + p.pop.toLocaleString('en-GB') : ''} · <a href="https://www.wikidata.org/wiki/${esc(p.qid)}" target="_blank" rel="noopener">Wikidata ${esc(p.qid)}</a></span>`;
    document.getElementById('hzSvg').innerHTML = '<p class="nt">Loading the skyline…</p>';
    profile(p).then(h => { document.getElementById('hzSvg').innerHTML = drawPanel(p, h); })
      .catch(() => { document.getElementById('hzSvg').innerHTML = '<p class="nt">The skyline could not load.</p>'; });
  }

  // ---------------- selecting a place: the skyline panel is the popup
  function select(qid, fly) {
    const p = byId[qid]; if (!p) return;
    fold(true);
    map.getSource('sel').setData({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [p.lon, p.lat] } }] });
    openPanel(p);
    if (fly) map.flyTo({ center: [p.lon, p.lat], zoom: Math.max(map.getZoom(), 11), duration: 1400, offset: small ? [0, -150] : [-120, -60] });
    const u = new URL(location.href); u.searchParams.set('place', qid); history.replaceState(null, '', u);
  }

  // ---------------- search
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let items = [], k = -1;
    const all = Object.values(byId).sort((a, b) => b.pop - a.pop);
    const show = () => {
      const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1;
      if (!v) { sug.style.display = 'none'; return; }
      const st = all.filter(p => norm(p.name).startsWith(v)), inn = all.filter(p => !norm(p.name).startsWith(v) && norm(p.name).includes(v));
      items = st.concat(inn).slice(0, 12);
      items.forEach((p, i) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(p.name)} <span>${esc(p.county)} · ${p.sol ? hm(p.sol) : 'no sun'} on 21 Dec</span>`;
        li.addEventListener('mousedown', e => { e.preventDefault(); pick(i); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none';
    };
    const pick = i => { const p = items[i]; if (!p) return; q.value = p.name; sug.style.display = 'none'; select(p.qid, true); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => {
      const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); }
      else if (e.key === 'Escape') sug.style.display = 'none';
    });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  // ---------------- the map layers
  function setRaster(name) {
    curRaster = name;
    for (const r in RASTERS) if (map.getLayer('r-' + r)) map.setLayoutProperty('r-' + r, 'visibility', r === name && document.getElementById('lyShade').checked ? 'visible' : 'none');
    document.querySelectorAll('.chip[data-r]').forEach(b => b.setAttribute('aria-pressed', b.dataset.r === name));
    document.querySelectorAll('.key').forEach(k => k.hidden = k.dataset.r !== name);
    const u = new URL(location.href); u.searchParams.set('layer', name); history.replaceState(null, '', u);
  }
  function setupLayers() {
    const before = (map.getStyle().layers.find(l => l.metadata && ['rivers', 'forests', 'mountains', 'names', 'heritage', 'roads'].includes(l.metadata.group)) || {}).id;
    const tiles = new URL('tiles/', location.href).href;
    for (const r in RASTERS) {
      map.addSource('r-' + r, { type: 'raster', tiles: [`${tiles}${r}/{z}/{x}/{y}.png`], tileSize: 256, minzoom: 5, maxzoom: 9, bounds: [BOUNDS[0][0], BOUNDS[0][1], BOUNDS[1][0], BOUNDS[1][1]],
        attribution: 'Terrain shadows: my calculation from AWS Terrain Tiles' });
      map.addLayer({ id: 'r-' + r, type: 'raster', source: 'r-' + r, layout: { visibility: 'none' },
        paint: { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.9, 8, 0.75, 10, 0.55, 13, 0.4], 'raster-resampling': 'nearest', 'raster-fade-duration': 0 } }, before);
    }
    const feats = Object.values(byId).map(p => ({ type: 'Feature', properties: { q: p.qid, n: p.name, s: p.flat ? (p.flat - p.sol) / p.flat : 0, d: (p.osm && p.osm[1] > 0) ? 0 : p.nod, pop: p.pop },
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] } }));
    map.addSource('pl', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Settlements: Wikidata (CC0)' });
    map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    const colour = ['case', ['>', ['get', 'd'], 0], '#1F1838', ['step', ['get', 's'], '#FBF1D2', 0.10, '#F2C46B', 0.25, '#E08A3C', 0.5, '#B5482E', 0.75, '#6E2547']];
    map.addLayer({ id: 'pl', type: 'circle', source: 'pl',
      filter: ['any', ['>', ['get', 'd'], 0], ['>=', ['zoom'], 9], ['all', ['>=', ['zoom'], 7], ['>=', ['get', 's'], 0.25]], ['>=', ['get', 's'], 0.5]],
      paint: { 'circle-color': colour, 'circle-stroke-color': '#2B2119', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 5, 0.6, 11, 1.3],
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, ['case', ['>', ['get', 'd'], 0], 3.4, 2], 9, ['case', ['>', ['get', 'd'], 0], 5.5, 3.5], 13, 7] } });
    map.addLayer({ id: 'sel', type: 'circle', source: 'sel', paint: { 'circle-radius': 11, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#A3261B', 'circle-stroke-width': 2.4 } });
    map.addLayer({ id: 'pln', type: 'symbol', source: 'pl', filter: ['any', ['>', ['get', 'd'], 0], ['>=', ['zoom'], 10.5]],
      layout: { 'text-field': ['get', 'n'], 'text-font': ['Ink Italic'], 'text-size': ['interpolate', ['linear'], ['zoom'], 6, 11, 12, 14], 'text-offset': [0, 0.9], 'text-anchor': 'top', 'text-optional': true,
        'symbol-sort-key': ['-', 0, ['get', 'd']] },
      minzoom: 7, paint: { 'text-color': '#1F1838', 'text-halo-color': 'rgba(251,245,228,0.95)', 'text-halo-width': 1.6 } });
    map.on('click', 'pl', e => { const f = e.features[0]; if (f) select(f.properties.q, false); });
    map.on('mouseenter', 'pl', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'pl', () => map.getCanvas().style.cursor = '');
    // layers panel
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', () => { const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.querySelectorAll('.chip[data-r]').forEach(b => b.addEventListener('click', () => setRaster(b.dataset.r)));
    document.querySelectorAll('input[name=rast]').forEach(b => b.addEventListener('change', () => { if (b.checked) setRaster(b.value); }));
    document.getElementById('lyShade').addEventListener('change', () => setRaster(curRaster));
    const vis = (id, on) => map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
    document.getElementById('lyPl').addEventListener('change', e => { vis('pl', e.target.checked); vis('pln', e.target.checked && document.getElementById('lyPln').checked); });
    document.getElementById('lyPln').addEventListener('change', e => vis('pln', e.target.checked && document.getElementById('lyPl').checked));
    const boxes = [...lp.querySelectorAll('input[data-g]')], modern = document.getElementById('modern');
    const base = () => {
      const m = modern.checked;
      boxes.forEach(b => { const g = b.dataset.g; const inkOnly = ['mountains', 'forests', 'sea', 'tint'].includes(g); try { InkMap.setGroup(map, g, b.checked && !(m && inkOnly)); } catch (e) { } });
      try { InkMap.setGroup(map, 'paper', !m); InkMap.setGroup(map, 'modern', m); InkMap.setGroup(map, 'coast', !m); if (m) InkMap.setGroup(map, 'roads', false); } catch (e) { }
    };
    boxes.forEach(b => b.addEventListener('change', base)); modern.addEventListener('change', base); base();
    document.querySelector(`input[name=rast][value=${curRaster}]`).checked = true;
    setRaster(curRaster);
  }

  // ---------------- start
  fetch('data/places.json').then(r => r.json()).then(j => {
    PL = j;
    j.places.forEach(a => { byId[a[0]] = { qid: a[0], name: a[1], lon: a[2], lat: a[3], sol: a[4], flat: a[5], nod: a[6], pop: a[7], nation: a[8], county: a[9], elev: a[10], osm: a[11] || null }; });
    const opts = { base: BASE, winter: false };
    if (qs.get('tj')) opts.tilejson = qs.get('tj');
    if (qs.get('dem')) opts.dem = qs.get('dem');
    if (qs.get('demmax')) opts.demMax = +qs.get('demmax');
    const at = (qs.get('at') || '').split(',').map(Number);
    opts.mapOptions = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: START, fitBoundsOptions: { padding: 6 } };
    return loadScripts(ENGINE).then(() => InkMap.create('map', opts));
  }).then(m => {
    map = m; m.__inkWinter = false; window.__map = m;
    const n = document.getElementById('nojs'); if (n) n.remove();
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    m.once('idle', foldAt); m.on('resize', () => setTimeout(foldAt, 50)); setTimeout(foldAt, 1500);
    setupLayers(); setupSearch();
    if (qs.get('place')) select(qs.get('place'), !qs.get('at'));
    const first = e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.hz,.mfs-btn,.maplibregl-ctrl')) return; fold(true); };
    document.getElementById('mapWrap').addEventListener('pointerdown', first, { capture: true, passive: true, once: true });
    document.querySelectorAll('a[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); select(a.dataset.go, true); }));
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
