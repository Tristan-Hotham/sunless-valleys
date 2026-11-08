"""Step 1: mosaic the zoom-10 terrarium tiles into one height grid (int16 metres, Web Mercator pixels) and a land mask.
Outputs in WORK: dem.npy (NY x NX int16), land.npy (bool), country.npy (uint8: 1 United Kingdom, 2 Ireland, 3 Isle of Man)."""
import numpy as np
from PIL import Image
from shapely.geometry import shape
from shapely.ops import transform as stransform
from rasterio.features import rasterize
from rasterio.transform import Affine
from common import *

dem = np.zeros((NY, NX), np.int16)
missing = 0
for tx in range(X0, X1 + 1):
    for ty in range(Y0, Y1 + 1):
        p = f"{TILES}/{tx}/{ty}.png"
        if not os.path.exists(p):
            missing += 1; continue
        a = np.asarray(Image.open(p).convert("RGB"), np.float32)
        h = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        dem[(ty - Y0) * 256:(ty - Y0 + 1) * 256, (tx - X0) * 256:(tx - X0 + 1) * 256] = np.clip(np.round(h), -32000, 32000).astype(np.int16)
print("missing tiles", missing, "height range", dem.min(), dem.max())

# The tiles carry a few spikes and pits (single cells or short streaks hundreds of metres off, e.g. 3,745 m in the
# Dornoch Firth and 1,660 m beside the Mournes). A spike would cast a false shadow and a pit would sit in a false valley,
# so replace any cell that stands more than 150 m off the median of its 7 x 7 neighbourhood, or more than 60 m above
# (below) the highest (lowest) of its 8 neighbours, by that median. Repeat until nothing changes.
from scipy.ndimage import median_filter, maximum_filter, minimum_filter
fp = np.ones((3, 3), bool); fp[1, 1] = False
d = dem.astype(np.float32); fixed = 0
for it in range(4):
    med = median_filter(d, size=7)
    nmax = maximum_filter(d, footprint=fp); nmin = minimum_filter(d, footprint=fp)
    bad = (np.abs(d - med) > 150) | (d - nmax > 60) | (nmin - d > 60)
    nb = int(bad.sum()); fixed += nb
    print("despike pass", it, nb)
    if not nb:
        break
    d[bad] = med[bad]
dem = np.round(d).astype(np.int16)
print("cells replaced", fixed, "new range", dem.min(), dem.max())

cs = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
ox, oy = X0 * 256, Y0 * 256
to_px = lambda x, y, z=None: tuple(np.asarray(v) for v in ((lambda X, Y: (X - ox, Y - oy))(*ll2px(x, y))))
country = np.zeros((NY, NX), np.uint8)
for code, iso in ((1, "GBR"), (2, "IRL"), (3, "IMN")):
    gs = [stransform(to_px, shape(f["geometry"])) for f in cs if f["properties"]["ADM0_A3"] == iso]
    m = rasterize([(g, code) for g in gs], out_shape=(NY, NX), transform=Affine.identity(), all_touched=False, dtype="uint8")
    country[m > 0] = code
# the Natural Earth coast is coarse: keep land cells that the terrain also puts above the sea (or in the Fens, just below)
land = (country > 0) & (dem > -8)
print("land cells", int(land.sum()), {c: int((country == c).sum()) for c in (1, 2, 3)})
jsave({"tiles": (X1 - X0 + 1) * (Y1 - Y0 + 1) - missing, "despiked": fixed}, f"{WORK}/dem_meta.json")
np.save(f"{WORK}/dem.npy", dem); np.save(f"{WORK}/land.npy", land); np.save(f"{WORK}/country.npy", country)
