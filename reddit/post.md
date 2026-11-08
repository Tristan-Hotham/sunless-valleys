**Title:** [OC] 64 places in the UK get no direct sunshine on the shortest day, because hills block the low winter sun. Kinlochleven goes 109 days without it

**Body:**

On 21 December the noon sun is only about 11 degrees up in central Scotland, so a steep hill to your south can hide it all day. I computed the skyline of every town, village and hamlet in the UK in Wikidata (36,692 places) from 90 m terrain, and drew the sun's path across each.

- 64 settlements get no direct sun on the solstice (41 in Scotland, 15 in Wales, 6 in England, 2 in Northern Ireland).
- Longest runs: Camas-luinie 123 days, Morvich 117, Kinlochleven 109. In the Lake District a hamlet called Seldom Seen gets 99 sunless days.
- I checked each sunless place again at its OpenStreetMap point: 20 of 84 Wikidata points got some sun there (often the Wikidata point sits up a shaded slope), so I left them out. That drops Penmaenmawr, the one town: its town centre keeps 1 h 39 min.
- Caveats: 90 m terrain, no buildings or trees, clear skies, one point per settlement. Treat single places as estimates.

Interactive map (tap any place for its skyline): https://maps.tristanhotham.com/sunless-valleys/

**Source comment:**

Data: AWS Terrain Tiles (zoom 10, Terrarium; chiefly SRTM), Wikidata settlements (CC0), Natural Earth. Tools: Python (numpy, numba, matplotlib), MapLibre. Method: horizon by ray tracing every degree to 30 km with Earth curvature and refraction; sun position from declination and latitude with refraction. Paper and code: https://github.com/Tristan-Hotham/sunless-valleys
