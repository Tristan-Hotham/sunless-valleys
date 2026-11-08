"""Step 10: README.md, LICENSE and reddit/post.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
kl, ss, pm = R["by_name"]["kinlochleven"], R["by_name"]["seldom_seen"], R["by_name"]["penmaenmawr"]
N = R["nations"]; G = R["grid"]; PC = R["point_check"]
top5 = "; ".join(f"{p['name']} ({p['county']}) {p['nodays']}" for p in R["top"][:6])
towns = "; ".join(f"{p['name']} {hm(p['lost_min'])} of {hm(p['flat_min'])}" for p in R["towns"][1:5])
readme = f"""# Britain's sunless valleys

Where hills hide the winter sun. The terrain horizon of every living settlement in the United Kingdom recorded in Wikidata ({R['n_sett']:,} places) and of {R['grid_cells']:,} land squares of about {R['grid_cell_m']:.0f} m covering Britain and Ireland, computed from the open AWS Terrain Tiles (about 90 m), combined with the sun's path to give the minutes of direct sun on 21 December and the number of days around the solstice with none.

Interactive page: https://maps.tristanhotham.com/sunless-valleys/
Paper: {{https://doi.org/10.5281/zenodo.24055580}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/sunless-valleys/}}
Code and data: https://github.com/Tristan-Hotham/sunless-valleys

## Headline results

- {R['zero_sol']} settlements get no direct sun on 21 December: {N['Scotland']['zero']} in Scotland, {N['Wales']['zero']} in Wales, {N['England']['zero']} in England and {N['Northern Ireland']['zero']} in Northern Ireland. {R['dark30']} of them go at least 30 days without it, {R['dark60']} at least 60 and {R['dark90']} at least 90.
- Longest runs of sunless days: {top5}.
- Kinlochleven (population {kl['pop']}, Wikidata) has a horizon {kl['hor_s']:.1f} degrees high due south against a solstice noon sun of {kl['noon_alt']:.1f} degrees: no direct sun for {kl['nodays']} days, about {kl['from']} to {kl['to']}. Seldom Seen in Glencoyne, near Glenridding: {ss['nodays']} days.
- Kinlochleven ({kl['pop']} people) is the largest settlement with no direct sun on the solstice. Penmaenmawr ({pm['pop']:,}) has none at its Wikidata point but keeps {hm(PC['by_qid']['Q2653611']['osm_sol_min'])} at its OpenStreetMap point in the town centre, so it is not counted. Among {R['n_towns2000']} places of 2,000 people or more, {R['towns_lost_2h']} lose two hours or more; e.g. {towns}.
- The count is checked (data/point_check.csv, code/11_point_check.py): {R['zero_pts']} Wikidata points get no direct sun, and separate code from the raw tiles with the NOAA solar position confirms {PC['check_zero']} of them. At the OpenStreetMap point for the same place (found for {PC['osm_matched']}), {PC['osm_zero']} stay sunless and {PC['osm_sunny']} get some sun; those {R['disputed']} are left out, giving {R['zero_sol']}.
- Against a flat horizon the median settlement loses {R['median_lost_min']:.0f} minutes on the solstice (Scotland {N['Scotland']['median_lost_min']:.0f}, Wales {N['Wales']['median_lost_min']:.0f}, England {N['England']['median_lost_min']:.0f}, Northern Ireland {N['Northern Ireland']['median_lost_min']:.0f}); {R['lost_hour_pc']:.0f}% lose an hour or more.
- Land: {G['United Kingdom']['zero_km2']:,.0f} km² of the UK ({G['Scotland']['zero_km2']:,.0f} km² in Scotland) and {G['Ireland']['zero_km2']:,.0f} km² of Ireland get no direct sun on 21 December.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page (built by `code/07_build_site.py`): The Inked World base map with three terrain-shadow layers, every settlement, search, and a skyline panel with the winter sun's path. |
| `header.png` | Social card, 1200 x 630. |
| `tiles/lost/`, `tiles/hours/`, `tiles/dark/` | Map tiles (palette PNG, zooms 5 to 9): share of solstice sunshine blocked; hours of direct sun on 21 December; days with no direct sun. |
| `data/settlements_sun.csv` | One row per settlement ({R['n_sett']:,}): Wikidata QID, name, type, nation, county, position, population, ground height, minutes of direct sun on 21 December, flat-horizon day length, minutes lost, sunless days (181 = at least 181), horizon due south, highest horizon between 120 and 240 degrees, noon solar altitude, and point_check (confirmed, disputed or unmatched) for the sunless points. |
| `data/sunless_places.csv` | The {R['zero_pts']} Wikidata points with no direct sun on the solstice, with the results of the check (the {R['disputed']} that get sun at their OpenStreetMap point are not counted). |
| `data/point_check.csv` | For each of them: an independent recomputation, and the result at the OpenStreetMap point of the same name (offset, minutes of sun, sunless days). |
| `data/prof/*.json` | Horizon profiles of every settlement (azimuth 60 to 300 every 2 degrees; base64 bytes, degrees = byte / 4 - 2), in 0.5 by 1 degree chunks. |
| `data/places.json`, `data/legend.json` | Page data. |
| `data/nation_grid_summary.csv` | Land areas in terrain shadow by nation, from the grid. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts, run in order, templates and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Terrain: zoom-10 Terrarium tiles x 481 to 517, y 291 to 348 joined into one grid (about 88 m at 55 N); {R['despiked']} spike and pit cells replaced by the 7 x 7 median; land = Natural Earth outline and height above -8 m.
- Horizon: rays every 1 degree from 60 to 300 (settlements, to 30 km, from 2 m above the ground at the Wikidata point) or every 2 degrees from 90 to 270 (grid, 175 m squares, to 20 km); samples from 80 m, stepping 80 m or 4%; bilinear heights; Earth curvature with refraction coefficient 0.13.
- Sun: declination by Cooper (1969) for each day from the solstice back to the equinox; altitude at each azimuth in closed form from latitude and declination; apparent altitude by Saemundsson's form of Bennett's refraction; time from the hour angle. Direct sun when the centre of the disc is above both the skyline and 0 degrees. Sunless days = 2k - 1 where offset k is the first day with sun (days after the solstice mirror those before).
- Settlements: Wikidata items with a living-settlement type (village, hamlet, town, suburb, locality, human settlement and similar), excluding forts, former or deserted villages, religious houses, camps and ski areas; one point per item.
- Caveats: 90 m terrain smooths ridges and gorges; no buildings or trees; one point per settlement; cloud ignored; refraction near the horizon varies; Wikidata coverage is uneven; Ireland is terrain only.

## How to rerun

Needs Python 3 with numpy, numba, mapbox-vector-tile, scipy, pandas, shapely, pyproj, rasterio, matplotlib and Pillow, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw input paths are in `code/common.py`; intermediates go to a work folder outside the repo (about 1 GB). Step 2 takes about an hour on two cores.

```
python3 code/01_dem.py          # terrain mosaic, despiking, land mask
python3 code/02_horizon.py      # horizons and sun for settlements and the grid
python3 code/03_places.py       # settlement table, page data, horizon profiles
python3 code/04_tiles.py        # map tiles
python3 code/05_results.py      # results.json and summaries
python3 code/11_point_check.py  # check of the sunless places at their OSM points (needs network), then run 05_results.py again
python3 code/06_figures.py      # figures and header
python3 code/07_build_site.py   # index.html
python3 code/08_paper.py        # paper PDF (set DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py       # collage
python3 code/10_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
```

## Sources and licences

- AWS Terrain Tiles (https://registry.opendata.aws/terrain-tiles/), Terrarium format, zoom 10. In Britain and Ireland chiefly SRTM (NASA/USGS, public domain), with ETOPO1 and GMTED at sea; attribution as listed at https://github.com/tilezen/joerd/blob/master/docs/attribution.md.
- Wikidata (https://www.wikidata.org/), CC0: UK settlements, coordinates, types and population.
- OpenStreetMap place points (via OpenFreeMap vector tiles), used only in the check; the OSM coordinates in data/point_check.csv are under the ODbL (https://www.openstreetmap.org/copyright).
- Natural Earth (public domain): land and country outlines. ONS county and nation boundaries (Open Government Licence v3.0).
- Base map on the page: The Inked World (https://maps.tristanhotham.com/ink-map/), OpenStreetMap vector tiles by OpenFreeMap (ODbL), AWS Terrain Tiles. Fonts: MedievalSharp, IM Fell (SIL OFL).
- Derived data, text and figures: CC BY 4.0. Code: MIT.

## Citation

Hotham, T. (2026) Britain's sunless valleys: where terrain hides the winter sun. Zenodo. {{https://doi.org/10.5281/zenodo.24055580}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures, the paper, the collage, the map tiles and the derived data in data/: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/.

The derived data come from the AWS Terrain Tiles (open data; chiefly SRTM, public domain) and Wikidata (CC0).
"""
post = f"""**Title:** [OC] {R['zero_sol']} places in the UK get no direct sunshine on the shortest day, because hills block the low winter sun. Kinlochleven goes {kl['nodays']} days without it

**Body:**

On 21 December the noon sun is only about {R['noon_alt_56']:.0f} degrees up in central Scotland, so a steep hill to your south can hide it all day. I computed the skyline of every town, village and hamlet in the UK in Wikidata ({R['n_sett']:,} places) from 90 m terrain, and drew the sun's path across each.

- {R['zero_sol']} settlements get no direct sun on the solstice ({N['Scotland']['zero']} in Scotland, {N['Wales']['zero']} in Wales, {N['England']['zero']} in England, {N['Northern Ireland']['zero']} in Northern Ireland).
- Longest runs: {R['top'][0]['name']} {R['top'][0]['nodays']} days, {R['top'][1]['name']} {R['top'][1]['nodays']}, Kinlochleven {kl['nodays']}. In the Lake District a hamlet called Seldom Seen gets {ss['nodays']} sunless days.
- I checked each sunless place again at its OpenStreetMap point: {R['disputed']} of {R['zero_pts']} Wikidata points got some sun there (often the Wikidata point sits up a shaded slope), so I left them out. That drops Penmaenmawr, the one town: its town centre keeps {hm(PC['by_qid']['Q2653611']['osm_sol_min'])}.
- Caveats: 90 m terrain, no buildings or trees, clear skies, one point per settlement. Treat single places as estimates.

Interactive map (tap any place for its skyline): https://maps.tristanhotham.com/sunless-valleys/

**Source comment:**

Data: AWS Terrain Tiles (zoom 10, Terrarium; chiefly SRTM), Wikidata settlements (CC0), Natural Earth. Tools: Python (numpy, numba, matplotlib), MapLibre. Method: horizon by ray tracing every degree to 30 km with Earth curvature and refraction; sun position from declination and latitude with refraction. Paper and code: https://github.com/Tristan-Hotham/sunless-valleys
"""
for txt in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in txt.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words")
