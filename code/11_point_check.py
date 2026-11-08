"""Step 11: an independent check of the sunless settlements, and of where their Wikidata points stand.

For each settlement with no direct sun on 21 December this step
  1. recomputes the horizon from the raw terrain tiles (no despiking) by stepping along great circles, and the sun by
     the NOAA solar position algorithm minute by minute on the real dates of the 2026/27 winter (so with the equation of
     time and the small asymmetry of the declination about the solstice): a check on code/02_horizon.py by a different
     route;
  2. looks up the OpenStreetMap place point with the same name within about 3 km (OpenFreeMap vector tiles, zoom 14)
     and repeats the computation there, since a Wikidata point a few hundred metres up a hillside can turn a sunny
     village into a sunless one;
  3. records how many decimals the Wikidata coordinate carries (2 decimals is about 1 km).
Output: data/point_check.csv (summary numbers also into data/results.json). Run after code/05_results.py, then run
05_results.py again: it counts a settlement as sunless only if it is also sunless at its OpenStreetMap point (where one
was found). Takes about 45 minutes; skipped if point_check.csv already covers the same settlements (RECHECK=1 forces it).
Needs network access to tiles.openfreemap.org and the mapbox-vector-tile package.
"""
import csv, math, os, re, sys, json, urllib.request, unicodedata, datetime as dt
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, DATA, SETT, TILES, jload, jsave
import mapbox_vector_tile as mvt


T = TILES
Z = 10; N = 256 * 2 ** Z
cache = {}

def tile(tx, ty):
    k = (tx, ty)
    if k not in cache:
        p = f"{T}/{tx}/{ty}.png"
        if not os.path.exists(p):
            cache[k] = None
        else:
            a = np.asarray(Image.open(p).convert("RGB"), np.float64)
            cache[k] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return cache[k]

def px(lon, lat):
    la = math.radians(lat)
    return (lon + 180) / 360 * N, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * N

def hgt_px(X, Y):
    tx, ty = int(X // 256), int(Y // 256)
    t = tile(tx, ty)
    if t is None: return None
    return t[int(Y) % 256, int(X) % 256]

def hgt(lon, lat):
    X, Y = px(lon, lat); X -= 0.5; Y -= 0.5
    x0, y0 = math.floor(X), math.floor(Y); fx, fy = X - x0, Y - y0
    v = [hgt_px(x0 + i, y0 + j) for j in (0, 1) for i in (0, 1)]
    if any(a is None for a in v): return None
    return (v[0] * (1 - fx) + v[1] * fx) * (1 - fy) + (v[2] * (1 - fx) + v[3] * fx) * fy

R = 6371000.0
def dest(lon, lat, az, d):
    p1, l1, a, dd = math.radians(lat), math.radians(lon), math.radians(az), d / R
    p2 = math.asin(math.sin(p1) * math.cos(dd) + math.cos(p1) * math.sin(dd) * math.cos(a))
    l2 = l1 + math.atan2(math.sin(a) * math.sin(dd) * math.cos(p1), math.cos(dd) - math.sin(p1) * math.sin(p2))
    return math.degrees(l2), math.degrees(p2)

def horizon(lon, lat, step=1.0, dmax=30000):
    h0 = hgt(lon, lat) + 2
    azs = np.arange(60, 300.01, step); out = []; where = []
    for az in azs:
        best, bd = -90, 0; d = 60.0
        while d < dmax:
            lo, la = dest(lon, lat, az, d)
            h = hgt(lo, la)
            if h is None: break
            ang = math.degrees(math.atan2(h - h0 - d * d * 0.87 / (2 * R), d))
            if ang > best: best, bd = ang, d
            d += max(45.0, 0.03 * d)
        out.append(best); where.append(bd)
    return azs, np.array(out), np.array(where), h0 - 2

def sunpos(lat, lon, t):
    """NOAA solar position; t UTC datetime. returns apparent elevation (deg), azimuth (deg from N)"""
    jd = t.timestamp() / 86400 + 2440587.5; T_ = (jd - 2451545) / 36525
    L0 = (280.46646 + T_ * (36000.76983 + 0.0003032 * T_)) % 360
    M = 357.52911 + T_ * (35999.05029 - 0.0001537 * T_)
    e = 0.016708634 - T_ * (0.000042037 + 0.0000001267 * T_)
    Mr = math.radians(M)
    C = math.sin(Mr) * (1.914602 - T_ * (0.004817 + 0.000014 * T_)) + math.sin(2 * Mr) * (0.019993 - 0.000101 * T_) + math.sin(3 * Mr) * 0.000289
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * T_))
    eps0 = 23 + (26 + (21.448 - T_ * (46.815 + T_ * (0.00059 - T_ * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * T_))
    dec = math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam)))
    y = math.tan(math.radians(eps / 2)) ** 2
    L0r = math.radians(L0)
    eqt = 4 * math.degrees(y * math.sin(2 * L0r) - 2 * e * math.sin(Mr) + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
                           - 0.5 * y * y * math.sin(4 * L0r) - 1.25 * e * e * math.sin(2 * Mr))
    mins = t.hour * 60 + t.minute + t.second / 60
    tst = mins + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    phi = math.radians(lat)
    cz = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
    el = 90 - math.degrees(math.acos(max(-1, min(1, cz))))
    az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(phi) - math.tan(dec) * math.cos(phi))) + 180) % 360
    if el > -0.575:
        te = math.tan(math.radians(el))
        r = (58.1 / te - 0.07 / te ** 3 + 0.000086 / te ** 5) if el > 5 else (1735 + el * (-518.2 + el * (103.4 + el * (-12.79 + el * 0.711))))
        el += r / 3600
    return el, az

def sun_minutes(lat, lon, azs, hor, day):
    m = 0
    for k in range(24 * 60):
        t = day + dt.timedelta(minutes=k)
        el, az = sunpos(lat, lon, t)
        if el <= 0 or az < 60 or az > 300: continue
        if el > np.interp(az, azs, hor): m += 1
    return m


import mapbox_vector_tile as mvt

URL = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers={"User-Agent": "sv-check"}), timeout=30))["tiles"][0]
ZT = 14; NT = 2 ** ZT

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())

def tilexy(lon, lat):
    la = math.radians(lat)
    return (lon + 180) / 360 * NT, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * NT

def xy2ll(X, Y):
    lon = X / NT * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y / NT))))
    return lon, lat

vcache = {}
def get(x, y):
    if (x, y) not in vcache:
        req = urllib.request.Request(URL.format(z=ZT, x=x, y=y), headers={"User-Agent": "sv-check"})
        try:
            data = urllib.request.urlopen(req, timeout=30).read()
            vcache[(x, y)] = mvt.decode(data)
        except Exception:
            vcache[(x, y)] = {}
    return vcache[(x, y)]

def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))



def nodays(lat, lon, azs, hor):
    sol = dt.datetime(2026, 12, 21, tzinfo=dt.timezone.utc)
    if sun_minutes(lat, lon, azs, hor, sol) > 0:
        return 0
    a = next((k for k in range(1, 91) if sun_minutes(lat, lon, azs, hor, sol - dt.timedelta(days=k)) > 0), 91)
    b = next((k for k in range(1, 91) if sun_minutes(lat, lon, azs, hor, sol + dt.timedelta(days=k)) > 0), 91)
    return a + b - 1


def run(lat, lon):
    azs, hor, wh, h0 = horizon(lon, lat)
    sol = dt.datetime(2026, 12, 21, tzinfo=dt.timezone.utc)
    return round(h0), sun_minutes(lat, lon, azs, hor, sol), nodays(lat, lon, azs, hor)


def osm_point(name, lon, lat):
    X, Y = tilexy(lon, lat); tx, ty = int(X), int(Y); best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            L = get(tx + dx, ty + dy).get("place")
            if not L: continue
            ext = L.get("extent", 4096)
            for f in L["features"]:
                p = f["properties"]
                if norm(name) not in (norm(p.get("name", "") or ""), norm(p.get("name:en", "") or "")): continue
                if f["geometry"]["type"] != "Point": continue
                px_, py_ = f["geometry"]["coordinates"]
                flon, flat = xy2ll(tx + dx + px_ / ext, ty + dy + 1 - py_ / ext)
                d = km(lat, lon, flat, flon)
                if best is None or d < best[0]:
                    best = (d, flat, flon, p.get("class", ""))
    return best


if __name__ == "__main__":
    prec = {}
    for line in open(SETT, encoding="utf-8"):
        m = re.match(r"<http://www.wikidata.org/entity/(Q\d+)>\t.*?POINT\(([-\d.]+) ([-\d.]+)\)", line)
        if m and m.group(1) not in prec:
            prec[m.group(1)] = min(len(v.rstrip("0").split(".")[1]) if "." in v else 0 for v in (m.group(2), m.group(3)))
    rows = list(csv.DictReader(open(f"{DATA}/sunless_places.csv", encoding="utf-8")))
    if os.path.exists(f"{DATA}/point_check.csv") and not os.environ.get("RECHECK"):
        have = {r["qid"] for r in csv.DictReader(open(f"{DATA}/point_check.csv", encoding="utf-8"))}
        if have == {r["qid"] for r in rows}:
            print("point_check.csv is up to date; set RECHECK=1 to recompute"); sys.exit(0)
    out = []
    for r in rows:
        lat, lon = float(r["lat"]), float(r["lon"])
        _, wsol, wnod = run(lat, lon)
        o = {"qid": r["qid"], "name": r["name"], "county": r["county"], "pop": r["pop"], "nodays": int(r["nodays"]),
             "wd_decimals": prec.get(r["qid"]), "check_sol_min": wsol, "check_nodays": wnod,
             "osm_class": "", "osm_offset_km": "", "osm_lat": "", "osm_lon": "", "osm_elev_m": "", "osm_sol_min": "", "osm_nodays": ""}
        b = osm_point(r["name"], lon, lat)
        if b:
            e, s, n = run(b[1], b[2])
            o.update(osm_class=b[3], osm_offset_km=round(b[0], 2), osm_lat=round(b[1], 5), osm_lon=round(b[2], 5), osm_elev_m=e, osm_sol_min=s, osm_nodays=n)
        out.append(o)
        print(o["name"], o["nodays"], o["check_nodays"], o["osm_offset_km"], o["osm_sol_min"], o["osm_nodays"], flush=True)
    with open(f"{DATA}/point_check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
    agree = [o for o in out if o["check_sol_min"] == 0]
    dd = [o["check_nodays"] - o["nodays"] for o in out]
    m = [o for o in out if o["osm_class"]]
    keep = [o for o in m if o["osm_sol_min"] == 0]
    R = jload(f"{DATA}/results.json")
    R["point_check"] = {"n": len(out), "check_zero": len(agree), "check_days_median_diff": float(np.median(dd)),
                        "check_days_mad": float(np.median(np.abs(dd))),
                        "osm_matched": len(m), "osm_zero": len(keep), "osm_sunny": len(m) - len(keep),
                        "osm_zero_names": [o["name"] for o in keep],
                        "osm_sunny_names": [o["name"] for o in m if o["osm_sol_min"] != 0],
                        "osm_offset_median_km": float(np.median([o["osm_offset_km"] for o in m])),
                        "coarse_2dp": sum(1 for o in out if (o["wd_decimals"] or 0) <= 2),
                        "by_qid": {o["qid"]: {k: o[k] for k in ("check_sol_min", "check_nodays", "osm_offset_km", "osm_sol_min", "osm_nodays", "osm_elev_m")} for o in out}}
    jsave(R, f"{DATA}/results.json", indent=1)
    print({k: v for k, v in R["point_check"].items() if k != "by_qid"})
