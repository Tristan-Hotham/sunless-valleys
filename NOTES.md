# sunless-valleys: working notes

Brief: /home/claude/work/new8/BRIEFS.md (study 6) + /home/claude/newdata/BRIEF.md. Format refs: studies/portolan-charts, colour-names.

## Plan
- 01_dem.py: mosaic AWS terrarium z10 tiles (x 481..517, y 291..348) into int16 metres, land mask from Natural Earth 10m (GB, IE, IM). Work files in /home/claude/work/new8/sunless-valleys/work (not in repo; delete at end).
- 02_horizon.py (numba): per land cell, horizon angle every 2 deg of azimuth 90..270 to 20 km (curvature + refraction k=0.13); then solstice minutes of direct sun, flat-horizon day length, days around solstice with no direct sun (capped at +-90 days). Settlements: finer (1 deg, 30 km, bilinear at exact point), profile 60..300 deg stored.
- Sun: NOAA-style declination; apparent centre altitude (Bennett refraction) vs horizon floored at 0.
- 03_tiles.py: raster tiles z5..9 palette PNG for map; 04 results; 05 site; 06 figures; 07 paper; 08 release; 09 readme; collage.

## Progress
- 01 done (993 cells despiked; land 38.8M cells). 02 settlements done (36,697 living settlements; 85 with no sun 21 Dec in first run).
  02 grid running (2x2 blocks, ~9.7M cells; ~1 h+ on shared CPU). CSV quoting bug fixed (QUOTE_NONE) after first run: rerun
  settlement part with SKIP_GRID=1 after the grid finishes, then 03..10.
- Written: 03_places, 04_tiles, 05_results, 06_figures (+sunfig.py), 07_build_site, 08_paper, 09_release, 10_readme, qa.js,
  reddit/collage.py, templates. To verify after data: Ireland counties claim in page s.04, Seldom Seen wording, top list areas.
- Species-places (study 5) STOPPED for data: see /home/claude/studies/species-places/NOTES.md.
- DONE (all steps, QA 0 console errors at 1280 and 390). Work folder deleted (rerun 01..02 to regenerate, ~25 min).
  Paper PDF shows https://doi.org/10.5281/zenodo.24055580: publisher reruns `DOI=10.5281/zenodo.N python3 code/08_paper.py` then 09_release.py.

## Independent review (2026)
- Method checked: Cooper declination, closed-form altitude by azimuth, Saemundsson refraction, curvature with k=0.13, 2k-1 run logic all correct.
- Added code/11_point_check.py -> data/point_check.csv + results.json "point_check": separate code (raw tiles, great-circle rays,
  NOAA solar position minute by minute) confirms 83/84 sunless points (runs ~2 days shorter, median). OSM place point of same name
  (OpenFreeMap z14) found for 58/84 (median 0.16 km away): 38 stay sunless, 20 get sun (incl. Penmaenmawr town centre 1 h 39 min,
  Aultbea, Talisker, Leirinmore, Kingairloch). Text now says the 84 are points, Penmaenmawr only partly shaded.
- Fixed: Kinlochleven's southern wall is Garbh Bheinn (the Mamores are to its north); Seldom Seen is in Glencoyne; Penmaenmawr
  sits east of the headland. Paper intro now cites Bristen (blue News), Rjukan mirrors (OPN 2013) and Solfest (Visit Rjukan).
- Figures/collage not rebuilt (need WORK files, ~1 h rerun of 01..02). Skyline figure title "Seldom Seen, Glenridding" kept.
- No formal published list of UK sunless places found (only anecdote, e.g. Guardian Country Diary on Lake District farms).
- Follow-up: reran 01..02 (grid identical: 4,956 km2 UK, 464 km2 Ireland). Headline now the checked count: 64 settlements
  (84 Wikidata points less 20 sunless only at the Wikidata point; 05_results.py reads data/point_check.csv; page popups
  flag the 20). Penmaenmawr dropped from counts/towns figure; skyline + collage panel now Penmaenpool. Work folder deleted.
  Pipeline order: 01 02 03 04 05 11 05 06 07 08 collage 10 09.
