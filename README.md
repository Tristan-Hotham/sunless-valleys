# Britain's sunless valleys

Where hills hide the winter sun. The terrain horizon of every living settlement in the United Kingdom recorded in Wikidata (36,692 places) and of 9,716,368 land squares of about 175 m covering Britain and Ireland, computed from the open AWS Terrain Tiles (about 90 m), combined with the sun's path to give the minutes of direct sun on 21 December and the number of days around the solstice with none.

Interactive page: https://maps.tristanhotham.com/sunless-valleys/
Paper: https://doi.org/10.5281/zenodo.24055580
Blog post: https://blog.tristanhotham.com/2026/10/31/sunless-valleys/
Code and data: https://github.com/Tristan-Hotham/sunless-valleys

## Headline results

- 64 settlements get no direct sun on 21 December: 41 in Scotland, 15 in Wales, 6 in England and 2 in Northern Ireland. 53 of them go at least 30 days without it, 27 at least 60 and 6 at least 90.
- Longest runs of sunless days: Camas-luinie (Highland) 123; Morvich (Highland) 117; Kinlochleven (Highland) 109; Camusnagaul (Highland) 103; Seldom Seen (Cumbria) 99; Ardessie (Highland) 91.
- Kinlochleven (population 810, Wikidata) has a horizon 25.6 degrees high due south against a solstice noon sun of 9.9 degrees: no direct sun for 109 days, about 28 October to 13 February. Seldom Seen in Glencoyne, near Glenridding: 99 days.
- Kinlochleven (810 people) is the largest settlement with no direct sun on the solstice. Penmaenmawr (4,353) has none at its Wikidata point but keeps 1 h 39 min at its OpenStreetMap point in the town centre, so it is not counted. Among 4589 places of 2,000 people or more, 46 lose two hours or more; e.g. Simmondley 3 h 42 min of 7 h 24 min; Ferndale 3 h 15 min of 7 h 43 min; Cymmer 3 h 09 min of 7 h 43 min; Abercarn 3 h 08 min of 7 h 43 min.
- The count is checked (data/point_check.csv, code/11_point_check.py): 84 Wikidata points get no direct sun, and separate code from the raw tiles with the NOAA solar position confirms 83 of them. At the OpenStreetMap point for the same place (found for 58), 38 stay sunless and 20 get some sun; those 20 are left out, giving 64.
- Against a flat horizon the median settlement loses 18 minutes on the solstice (Scotland 41, Wales 41, England 14, Northern Ireland 23); 14% lose an hour or more.
- Land: 4,956 km² of the UK (4,450 km² in Scotland) and 464 km² of Ireland get no direct sun on 21 December.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page (built by `code/07_build_site.py`): The Inked World base map with three terrain-shadow layers, every settlement, search, and a skyline panel with the winter sun's path. |
| `header.png` | Social card, 1200 x 630. |
| `tiles/lost/`, `tiles/hours/`, `tiles/dark/` | Map tiles (palette PNG, zooms 5 to 9): share of solstice sunshine blocked; hours of direct sun on 21 December; days with no direct sun. |
| `data/settlements_sun.csv` | One row per settlement (36,692): Wikidata QID, name, type, nation, county, position, population, ground height, minutes of direct sun on 21 December, flat-horizon day length, minutes lost, sunless days (181 = at least 181), horizon due south, highest horizon between 120 and 240 degrees, noon solar altitude, and point_check (confirmed, disputed or unmatched) for the sunless points. |
| `data/sunless_places.csv` | The 84 Wikidata points with no direct sun on the solstice, with the results of the check (the 20 that get sun at their OpenStreetMap point are not counted). |
| `data/point_check.csv` | For each of them: an independent recomputation, and the result at the OpenStreetMap point of the same name (offset, minutes of sun, sunless days). |
| `data/prof/*.json` | Horizon profiles of every settlement (azimuth 60 to 300 every 2 degrees; base64 bytes, degrees = byte / 4 - 2), in 0.5 by 1 degree chunks. |
| `data/places.json`, `data/legend.json` | Page data. |
| `data/nation_grid_summary.csv` | Land areas in terrain shadow by nation, from the grid. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts, run in order, templates and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Terrain: zoom-10 Terrarium tiles x 481 to 517, y 291 to 348 joined into one grid (about 88 m at 55 N); 993 spike and pit cells replaced by the 7 x 7 median; land = Natural Earth outline and height above -8 m.
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

Hotham, T. (2026) Britain's sunless valleys: where terrain hides the winter sun. Zenodo. https://doi.org/10.5281/zenodo.24055580

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
