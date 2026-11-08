"""Step 2: the terrain horizon and the winter sun, for every land cell and for every settlement.

For each land cell of the zoom-10 grid (about 90 m across in Britain) the horizon angle is found every 2 degrees of
azimuth from due east (90) through south to due west (270), out to 20 km, allowing for the curvature of the Earth and
standard terrestrial refraction (k = 0.13). Each settlement gets the same at its exact Wikidata point, every 1 degree
from 60 to 300, out to 30 km, with an observer 2 m above the ground.

The sun: for each day from the winter solstice back to the equinox (offsets 0 to 90 days; the days after the solstice
mirror them to within a fraction of a degree of declination), the sun's altitude at each azimuth follows from the
declination (Cooper's formula) and the latitude, and the time it takes to move between azimuths from the hour angle.
Altitudes are apparent (Bennett's refraction). The sun counts as shining on a place when the centre of its disc is
above both the terrain horizon and the flat horizon (0 degrees). So:
  sol_min   minutes of direct sun on 21 December
  flat_min  the length of the day with a flat horizon (sun above 0 degrees), the same for every cell in a row
  nodays    the number of days around the solstice with no direct sun at all (2k-1 when day offset k is the first that
            gets sun; 181 means none within 90 days either side, reported as "at least")
Outputs in WORK: sol_min.npy (uint16, 65535 = not land), nodays.npy (uint8, 255 = not land), flat_min_row.npy.
Settlements: data/settlements_sun.csv and WORK/sett_profiles.npy.
"""
import time, csv
import numpy as np
import numba as nb
from common import *

# ---------------- the sun
def decl(k):
    """declination (degrees) k days before 21 December (day of year 355), Cooper (1969)"""
    N = 355 - np.asarray(k, float)
    return -23.44 * np.cos(np.radians(360.0 / 365.0 * (N + 10)))


def bennett(h):
    """refraction in degrees for true altitude h (degrees), Bennett (1982) via Saemundsson's inverse form"""
    h = np.maximum(h, -1.5)
    return (1.02 / np.tan(np.radians(h + 10.3 / (h + 5.11)))) / 60.0


def sun_table(lat, az):
    """apparent altitude (deg) and minutes spent per azimuth bin, for each day offset 0..90.
    az: bin edges (deg). Returns alt at bin centres [NDAYS, nbins] and dt [NDAYS, nbins] (minutes, 0 where the sun is
    below the flat horizon at both edges)."""
    phi = np.radians(lat)
    d = np.radians(decl(np.arange(NDAYS)))[:, None]
    A = np.radians(np.asarray(az, float))[None, :]
    a, b = np.sin(phi), np.cos(phi) * np.cos(A)
    r = np.sqrt(a * a + b * b); psi = np.arctan2(b, a)
    h = np.arcsin(np.clip(np.sin(d) / r, -1, 1)) - psi                      # true altitude at each azimuth
    cosH = (np.sin(h) - np.sin(phi) * np.sin(d)) / (np.cos(phi) * np.cos(d))
    H = np.degrees(np.arccos(np.clip(cosH, -1, 1))) * np.where(A < np.pi, -1, 1)   # hour angle, morning negative
    t = H / 15.0 * 60.0                                                       # minutes from solar noon
    hd = np.degrees(h)
    app = hd + bennett(hd)
    # minutes in each bin while the sun is above the flat horizon: clip the time span to the part with app > 0
    tc = 0.5 * (t[:, 1:] + t[:, :-1]); dt = t[:, 1:] - t[:, :-1]
    ac = 0.5 * (app[:, 1:] + app[:, :-1])
    # partial bins at sunrise/sunset: linear fraction above 0
    a0, a1 = app[:, :-1], app[:, 1:]
    frac = np.where((a0 > 0) & (a1 > 0), 1.0, np.where((a0 <= 0) & (a1 <= 0), 0.0,
                    np.clip(np.maximum(a0, a1) / np.maximum(np.abs(a1 - a0), 1e-9), 0, 1)))
    return ac.astype(np.float32), (dt * frac).astype(np.float32), app.astype(np.float32)


# ---------------- the horizon (numba)
def ray_distances(dmax):
    d, out = 80.0, []
    while d <= dmax:
        out.append(d); d += max(80.0, 0.04 * d)
    return np.array(out, np.float64)


@nb.njit(inline="always")
def bil(dem, y, x):
    ny, nx = dem.shape
    if x < 0 or y < 0 or x >= nx - 1 or y >= ny - 1:
        return -1e9
    x0 = int(x); y0 = int(y); fx = x - x0; fy = y - y0
    a = dem[y0, x0]; b = dem[y0, x0 + 1]; c = dem[y0 + 1, x0]; e = dem[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + e * fx) * fy


@nb.njit(inline="always")
def horizon_at(dem, y, x, h0, scale, sa, ca, D, reff2):
    """horizon tangent along one azimuth from fractional pixel (y, x); scale = metres per pixel"""
    best = -1e9
    for i in range(D.shape[0]):
        d = D[i]
        p = d / scale
        hs = bil(dem, y - ca * p, x + sa * p)          # north is -y
        if hs < -1e8:
            break
        t = (hs - h0 - d * d / reff2) / d
        if t > best:
            best = t
    return best


@nb.njit(parallel=True)
def grid_sun(dem, land, rowscale, rowband, AZ, D, reff2, ALTc, DT, NSUB):
    """per output cell (a 2 x 2 block of zoom-10 pixels, i.e. one zoom-9 pixel, about 175 m in
    Britain, observed from its centre): minutes of sun on the solstice and number of sunless days. AZ: grid azimuths
    (deg); ALTc/DT [band, day, sub-bin] where sub-bins split each 2-degree gap into NSUB parts."""
    ny, nx = dem.shape[0] // 2, dem.shape[1] // 2
    sol = np.full((ny, nx), 65535, np.uint16)
    nod = np.full((ny, nx), 255, np.uint8)
    naz = AZ.shape[0]
    sa = np.sin(np.radians(AZ)); ca = np.cos(np.radians(AZ))
    nbin = ALTc.shape[2]
    for y in nb.prange(ny):
        Y = 2 * y
        sc = rowscale[Y]; band = rowband[Y]
        hor = np.empty(naz, np.float64)
        hb = np.empty(nbin, np.float64)
        for x in range(nx):
            X = 2 * x
            if int(land[Y, X]) + int(land[Y + 1, X]) + int(land[Y, X + 1]) + int(land[Y + 1, X + 1]) < 2:
                continue
            h0 = 0.25 * (float(dem[Y, X]) + dem[Y + 1, X] + dem[Y, X + 1] + dem[Y + 1, X + 1]) + 2.0
            for j in range(naz):
                hor[j] = np.degrees(np.arctan(horizon_at(dem, Y + 0.5, X + 0.5, h0, sc, sa[j], ca[j], D, reff2)))
            # horizon at the sub-bin centres, floored at the flat horizon
            for j in range(nbin):
                f = (j + 0.5) / NSUB; i0 = int(f); w = f - i0
                v = hor[i0] * (1 - w) + hor[min(i0 + 1, naz - 1)] * w
                hb[j] = v if v > 0 else 0.0
            m = 0.0
            for j in range(nbin):
                if ALTc[band, 0, j] > hb[j]:
                    m += DT[band, 0, j]
            sol[y, x] = int(m + 0.5)
            k = 0
            if m <= 0:
                k = 1
                while k < ALTc.shape[1]:
                    lit = False
                    for j in range(nbin):
                        if DT[band, k, j] > 0 and ALTc[band, k, j] > hb[j]:
                            lit = True; break
                    if lit:
                        break
                    k += 1
            nod[y, x] = 0 if k == 0 else (2 * k - 1 if k < ALTc.shape[1] else 181)
    return sol, nod


@nb.njit(parallel=True)
def point_horizons(dem, ys, xs, h0s, scales, AZ, D, reff2):
    n = ys.shape[0]; naz = AZ.shape[0]
    out = np.empty((n, naz), np.float32)
    sa = np.sin(np.radians(AZ)); ca = np.cos(np.radians(AZ))
    for i in nb.prange(n):
        for j in range(naz):
            out[i, j] = np.degrees(np.arctan(horizon_at(dem, ys[i], xs[i], h0s[i], scales[i], sa[j], ca[j], D, reff2)))
    return out


def main():
    dem = np.load(f"{WORK}/dem.npy")
    land = np.load(f"{WORK}/land.npy")
    reff2 = 2 * R_EARTH / (1 - K_REFR)
    ys = np.arange(NY) + Y0 * 256 + 0.5
    _, lat_rows = px2ll(np.zeros(NY), ys)
    rowscale = PIX0 * np.cos(np.radians(lat_rows))
    # latitude bands of 0.02 degrees for the sun tables
    lat_lo = float(lat_rows.min()) - 0.01
    rowband = np.floor((lat_rows - lat_lo) / 0.02).astype(np.int32)
    nb_ = rowband.max() + 1
    NSUB = 4
    AZ = np.arange(AZ0, AZ1 + 1e-9, DAZ)
    edges = np.linspace(AZ0, AZ1, (len(AZ) - 1) * NSUB + 1)
    ALTc = np.zeros((nb_, NDAYS, len(edges) - 1), np.float32); DT = np.zeros_like(ALTc)
    flat = np.zeros(nb_)
    for b in range(nb_):
        a, dt, _ = sun_table(lat_lo + (b + 0.5) * 0.02, edges)
        ALTc[b], DT[b] = a, dt
        flat[b] = dt[0][a[0] > 0].sum()
    np.save(f"{WORK}/flat_min_row.npy", flat[rowband].astype(np.float32))
    D = ray_distances(DMAX_GRID)
    print("rays", len(D), "samples; bands", nb_, "; flat day length", flat.min(), flat.max())

    # ---- settlements first (fast, and a check of the method)
    rows = []
    with open(SETT, encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE); next(r)
        for p in r:
            m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", p[2])
            if not m: continue
            qid = p[0].rsplit("/", 1)[-1].rstrip(">"); name = lit(p[1])
            pop = float(p[3]) if p[3] else None
            typ = lit(p[4]) if len(p) > 4 else ""
            rows.append((qid, name, float(m.group(1)), float(m.group(2)), pop, typ))
    # one row per item: keep the first coordinate; collect the types
    seen = {}
    for q, n, lon, lat, pop, typ in rows:
        if q not in seen:
            seen[q] = [q, n, lon, lat, pop, {typ} if typ else set()]
        else:
            if typ: seen[q][5].add(typ)
            if pop and not seen[q][4]: seen[q][4] = pop
    S = [s for s in seen.values() if living(s[5])]
    lon = np.array([s[2] for s in S]); lat = np.array([s[3] for s in S])
    X, Y = ll2px(lon, lat); xs = X - X0 * 256 - 0.5; ys_ = Y - Y0 * 256 - 0.5
    ok = (xs >= 1) & (ys_ >= 1) & (xs < NX - 2) & (ys_ < NY - 2)
    xi, yi = np.clip(np.round(xs).astype(int), 0, NX - 1), np.clip(np.round(ys_).astype(int), 0, NY - 1)
    ok &= land[yi, xi] | land[np.clip(yi + 1, 0, NY - 1), xi] | land[np.clip(yi - 1, 0, NY - 1), xi] | land[yi, np.clip(xi + 1, 0, NX - 1)] | land[yi, np.clip(xi - 1, 0, NX - 1)]
    S = [s for s, o in zip(S, ok) if o]; xs, ys_, lon, lat = xs[ok], ys_[ok], lon[ok], lat[ok]
    print("settlements", len(rows), "rows", len(seen), "items", len(S), "on land in the grid")
    h0 = np.array([max(0.0, float(bil_py(dem, y, x))) for y, x in zip(ys_, xs)]) + 2.0
    sc = PIX0 * np.cos(np.radians(lat))
    SAZ = np.arange(SAZ0, SAZ1 + 1e-9, SDAZ)
    t0 = time.time()
    P = point_horizons(dem, ys_, xs, h0, sc, SAZ, ray_distances(DMAX_SETT), reff2)
    print("settlement horizons", round(time.time() - t0), "s")
    np.save(f"{WORK}/sett_profiles.npy", P)
    # sun for each settlement at 0.25-degree sub-bins
    sedges = np.arange(SAZ0, SAZ1 + 1e-9, 0.25)
    out = []
    for i, s in enumerate(S):
        a, dt, _ = sun_table(lat[i], sedges)
        hc = np.interp(0.5 * (sedges[1:] + sedges[:-1]), SAZ, P[i]); hc = np.maximum(hc, 0)
        sunny = (a > hc[None, :]) & (dt > 0)
        mins = (dt * sunny).sum(1); flatm = (dt * (a > 0)).sum(1)
        k = int(np.argmax(mins > 0)) if (mins > 0).any() else NDAYS
        nod = 0 if k == 0 else (2 * k - 1 if k < NDAYS else 181)
        noon = a[0][np.argmin(np.abs(0.5 * (sedges[1:] + sedges[:-1]) - 180))]
        out.append({"qid": s[0], "name": s[1], "lon": round(lon[i], 5), "lat": round(lat[i], 5), "pop": s[4],
                    "type": "; ".join(sorted(s[5])), "elev_m": round(h0[i] - 2.0),
                    "sol_min": round(float(mins[0]), 1), "flat_min": round(float(flatm[0]), 1),
                    "lost_min": round(float(flatm[0] - mins[0]), 1), "nodays": nod,
                    "hor_s": round(float(np.interp(180, SAZ, P[i])), 2), "noon_alt": round(float(noon), 2),
                    "hor_max": round(float(P[i][(SAZ >= 120) & (SAZ <= 240)].max()), 2)})
    keys = list(out[0].keys())
    with open(f"{WORK}/settlements_sun.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(out)
    print("settlements done; with no sun on 21 Dec:", sum(o["sol_min"] == 0 for o in out))

    if os.environ.get("SKIP_GRID"):
        return
    t0 = time.time()
    sol, nod = grid_sun(dem, land, rowscale, rowband, AZ, D, reff2, ALTc, DT, NSUB)
    print("grid", round(time.time() - t0), "s")
    np.save(f"{WORK}/sol_min.npy", sol); np.save(f"{WORK}/nodays.npy", nod)


def lit(v):
    m = re.match(r'^"(.*)"(@[\w-]+)?$', v.strip())
    return m.group(1) if m else v.strip()


KEEP_T = re.compile(r"village|hamlet|human settlement|suburb|town|city|locality|area of london|neighbo|housing|resort|"
                    r"urban area|residential|township|conurbation|built-up|quarter|crofting|community", re.I)
DROP_T = re.compile(r"deserted|former|abandoned|lost|medieval|roman|shrunken|site|fort|camp|ruin|castr|castell|ski", re.I)


def living(types):
    """a place people live in now: at least one type that names a settlement and is not a former or archaeological one"""
    return any(KEEP_T.search(t) and not DROP_T.search(t) for t in types)


def bil_py(dem, y, x):
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    a, b, c, e = (float(v) for v in (dem[y0, x0], dem[y0, x0 + 1], dem[y0 + 1, x0], dem[y0 + 1, x0 + 1]))
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + e * fx) * fy


if __name__ == "__main__":
    main()
