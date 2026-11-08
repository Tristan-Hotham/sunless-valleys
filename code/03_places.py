"""Step 3: the settlements for the page and the data folder.
Adds nation and county (point in polygon, nearest polygon within 2 km for points on the shore), writes
  data/settlements_sun.csv     every living settlement: sun on 21 December, flat-horizon day, minutes lost, days without sun
  data/places.json             the same, compact, for the map
  data/prof/<lat>_<lon>.json   horizon profiles (every 2 degrees from 60 to 300) in 0.5 x 1 degree chunks, for the panel
"""
import base64, csv
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

S = list(csv.DictReader(open(f"{WORK}/settlements_sun.csv", encoding="utf-8")))
P = np.load(f"{WORK}/sett_profiles.npy")
assert len(S) == P.shape[0]
SAZ = np.arange(SAZ0, SAZ1 + 1e-9, SDAZ)

feats = jload(f"{GEO}/counties_uk.geojson")["features"]
geoms = [shape(f["geometry"]) for f in feats]
tree = STRtree(geoms)
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]
out, prof = [], {}
for i, s in enumerate(S):
    lon, lat = float(s["lon"]), float(s["lat"])
    pt = Point(lon, lat)
    hit = [j for j in tree.query(pt) if geoms[j].contains(pt)]
    if not hit:
        j = int(tree.nearest(pt))
        if geoms[j].distance(pt) * 111 > 2:
            j = None
    else:
        j = hit[0]
    nation = feats[j]["properties"]["nation"] if j is not None else ""
    county = feats[j]["properties"]["county"] if j is not None else ""
    s.update(nation=nation, county=county)
    pr = P[i][::2]                                    # 60..300 every 2 degrees
    q = np.clip(np.round((pr + 2) * 4), 0, 255).astype(np.uint8)
    key = f"{math.floor(lat * 2) / 2:.1f}_{math.floor(lon):d}"
    prof.setdefault(key, {})[s["qid"]] = base64.b64encode(q.tobytes()).decode()
    out.append(s)

print("no nation:", sum(1 for s in out if not s["nation"]), [s["name"] for s in out if not s["nation"]][:10])
keys = ["qid", "name", "type", "nation", "county", "lon", "lat", "pop", "elev_m", "sol_min", "flat_min", "lost_min", "nodays",
        "hor_s", "hor_max", "noon_alt"]
with open(f"{DATA}/settlements_sun.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, keys, extrasaction="ignore"); w.writeheader(); w.writerows(out)
# compact list for the map, worst first so the darkest draw on top
num = lambda v: float(v) if v not in ("", None) else 0.0
PCK = {}
if os.path.exists(f"{DATA}/point_check.csv"):          # code/11_point_check.py: the result at the OpenStreetMap point
    for r in csv.DictReader(open(f"{DATA}/point_check.csv", encoding="utf-8")):
        if r["osm_offset_km"] != "":
            PCK[r["qid"]] = [float(r["osm_offset_km"]), int(float(r["osm_sol_min"])), int(float(r["osm_nodays"]))]
rows = sorted(out, key=lambda s: (num(s["lost_min"]) / max(num(s["flat_min"]), 1), int(s["nodays"])))
places = [[s["qid"], s["name"], round(num(s["lon"]), 4), round(num(s["lat"]), 4), round(num(s["sol_min"])), round(num(s["flat_min"])),
           int(s["nodays"]), int(num(s["pop"])) if s["pop"] else 0, NATIONS.index(s["nation"]) if s["nation"] in NATIONS else -1,
           s["county"], int(num(s["elev_m"]))] + ([PCK[s["qid"]]] if s["qid"] in PCK else []) for s in rows]
jsave({"fields": ["qid", "name", "lon", "lat", "sol_min", "flat_min", "nodays", "pop", "nation", "county", "elev_m", "osm_check"],
       "nations": NATIONS, "places": places}, f"{DATA}/places.json")
pdir = f"{DATA}/prof"
os.makedirs(pdir, exist_ok=True)
for fn in os.listdir(pdir):
    os.remove(os.path.join(pdir, fn))
for k, v in prof.items():
    jsave(v, f"{pdir}/{k}.json")
print("places", len(places), "profile chunks", len(prof), "size KB", sum(os.path.getsize(os.path.join(pdir, f)) for f in os.listdir(pdir)) // 1024,
      "places.json KB", os.path.getsize(f"{DATA}/places.json") // 1024)
