"""Shared paths, constants and helpers for the sunless-valleys study ("Britain's sunless valleys").

Raw inputs (read in place, never modified):
  TILES  /home/claude/newdata/raw_new8/terrain/tiles/10/{x}/{y}.png
         AWS Terrain Tiles (Mapzen "terrarium" encoding: height = R*256 + G + B/256 - 32768 metres), zoom 10, x 481..517,
         y 291..348 (Britain and Ireland, lon -10.8 to 2.0, lat 49.8 to 61.0). https://registry.opendata.aws/terrain-tiles/
         Sources in this area are chiefly SRTM and, at sea, ETOPO1/GMTED; open data, attribution required (see README).
  SETT   /home/claude/newdata/raw_new8/uk_settlements.tsv
         Wikidata (CC0): UK settlements with coordinates, population and type (columns ?p ?pl ?coord ?pop ?typel).
  GEO    /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson (land mask), ne_50m_land.geojson (figures),
         counties_uk.geojson (county of each settlement). Natural Earth, public domain; ONS boundaries, OGL v3.
Intermediates (DEM mosaic, per-cell rasters) go to WORK, outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = os.environ.get("SV_TILES", "/home/claude/newdata/raw_new8/terrain/tiles/10")
SETT = os.environ.get("SV_SETT", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
GEO = os.environ.get("SV_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("SV_FONTS", "/home/claude/ref/fonts")
INK = os.environ.get("SV_INK", "/home/claude/studies/ink-map")
INKFONTS = os.path.join(INK, "fonts", "ttf")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.environ.get("SV_WORK", "/home/claude/work/new8/sunless-valleys/work")
for d in (DATA, IMG, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "sunless-valleys"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
TERRAIN_URL = "https://registry.opendata.aws/terrain-tiles/"
TERRAIN_ATTR = "https://github.com/tilezen/joerd/blob/master/docs/attribution.md"

# the tile block
Z = 10
X0, X1, Y0, Y1 = 481, 517, 291, 348          # inclusive
NX, NY = (X1 - X0 + 1) * 256, (Y1 - Y0 + 1) * 256
R_EARTH = 6371008.8
K_REFR = 0.13                                  # standard terrestrial refraction coefficient
C_MERC = 2 * math.pi * 6378137.0               # Web Mercator equator length
PIX0 = C_MERC / (256 * 2 ** Z)                 # metres per pixel at the equator (152.87 m)

# horizon sampling for the grid and for settlements
AZ0, AZ1, DAZ = 90.0, 270.0, 2.0                # grid: 91 azimuths
SAZ0, SAZ1, SDAZ = 60.0, 300.0, 1.0             # settlements: 241 azimuths
DMAX_GRID, DMAX_SETT = 20000.0, 30000.0
NDAYS = 91                                      # days 0..90 either side of the solstice


def px2ll(X, Y):
    """global z10 pixel coordinates (pixel centres at +0.5) to lon, lat"""
    import numpy as np
    n = 256 * 2 ** Z
    lon = np.asarray(X, float) / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * np.asarray(Y, float) / n))))
    return lon, lat


def ll2px(lon, lat):
    import numpy as np
    n = 256 * 2 ** Z
    lat = np.radians(np.asarray(lat, float))
    return (np.asarray(lon, float) + 180.0) / 360.0 * n, (1 - np.log(np.tan(lat) + 1 / np.cos(lat)) / np.pi) / 2 * n


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "hm": return hm(v)
    raise ValueError(f)


def hm(minutes):
    """minutes as 'H h MM min' style words: '6 h 49 min', '0 min'"""
    m = int(round(float(minutes)))
    h, mm = divmod(m, 60)
    return f"{h} h {mm:02d} min" if h else f"{mm} min"


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))
