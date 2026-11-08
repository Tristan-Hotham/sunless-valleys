"""Shared figure pieces for code/06_figures.py and reddit/collage.py: the overview map, the skyline panel, the
lost-sunshine colours and the Web Mercator helpers."""
import numpy as np, pandas as pd
from PIL import Image
from matplotlib.colors import ListedColormap, BoundaryNorm, LightSource
import matplotlib.patheffects as pe
from figstyle import *
import importlib.util

spec = importlib.util.spec_from_file_location("h", os.path.join(ROOT, "code", "02_horizon.py")); H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
Image.MAX_IMAGE_PIXELS = None
R = jload(f"{DATA}/results.json")
LG = jload(f"{DATA}/legend.json")
S = pd.read_csv(f"{DATA}/settlements_sun.csv")
P = np.load(f"{WORK}/sett_profiles.npy")
RAWS = pd.read_csv(f"{WORK}/settlements_sun.csv")
assert len(RAWS) == len(S) and (RAWS.qid.values == S.qid.values).all()
SAZ = np.arange(SAZ0, SAZ1 + 1e-9, SDAZ)
# sunless = no sun at the Wikidata point and not contradicted at the OpenStreetMap point (code/11_point_check.py)
S["sunless"] = (S.nodays > 0) & (S["point_check"].fillna("") != "disputed")
HALO = [pe.withStroke(linewidth=3.2, foreground=PAPER)]
C = C_MERC


def px2m(X, Y, z):
    n = 256 * 2 ** z
    return np.asarray(X) / n * C - C / 2, C / 2 - np.asarray(Y) / n * C


def ll2m(lon, lat):
    X, Y = ll2px(lon, lat)
    return px2m(X, Y, Z)


lostf = np.load(f"{WORK}/lostf.npy")
LCM = ListedColormap(["#00000000"] + LG["lost"]["colours"])
LNORM = BoundaryNorm([-1] + LG["lost"]["breaks"] + [2], LCM.N)


def lost_rgba(a, alpha=0.9):
    v = np.nan_to_num(a, nan=-1)
    rgba = LCM(LNORM(v)); rgba[..., 3] = np.where(v >= LG["lost"]["breaks"][0], alpha, 0)
    return rgba


# ---------- 1. the overview map
def overview(ax, k=2, dots=True, labels=True):
    ext, f = ink_base(ax, 3857, (-10.6, 2.0, 49.85, 60.95), coast_lw=0.6, ripple_m=(6e3, 15e3, 28e3))
    a = lostf
    h, w = a.shape[0] // k * k, a.shape[1] // k * k
    import warnings; warnings.simplefilter("ignore")
    b = np.nanmax(a[:h, :w].reshape(h // k, k, w // k, k), axis=(1, 3))
    x0, y0 = px2m(X0 * 128, Y0 * 128, 9); x1, y1 = px2m(X0 * 128 + w, Y0 * 128 + h, 9)
    ax.imshow(lost_rgba(b, 0.95), extent=(x0, x1, y1, y0), zorder=3.5, interpolation="nearest")
    if dots:
        z = S[S.sunless].sort_values("nodays")
        mx, my = ll2m(z.lon.values, z.lat.values)
        ax.scatter(mx, my, s=6 + z.nodays.values * 0.45, c="#1F1838", edgecolors=PAPER, linewidths=0.7, zorder=6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    return ext


# ---------- 2. skylines
def idx(name, county):
    m = S[(S["name"] == name) & (S.county == county)]
    return int(m.index[0])


def skyline(ax, i, title, top=32):
    s = S.loc[i]; lat = s.lat
    hor = P[i]
    a, dt, app = H.sun_table(lat, SAZ)
    az = SAZ
    for k, col, ls, lw in ((61, "#B8862B", (0, (4, 3)), 1.2), (31, "#C77A2A", (0, (4, 3)), 1.2), (0, RED, "-", 2.0)):
        m = app[k] > -1
        ax.plot(az[m], app[k][m], color=col, ls=ls, lw=lw, zorder=3)
    ax.fill_between(az, -2, np.maximum(hor, -2), color=INKC, alpha=0.85, lw=0, zorder=4)
    ax.plot(az, hor, color=INKC, lw=0.8, zorder=4)
    vis = (app[0] > np.maximum(hor, 0))
    y = np.where(vis, app[0], np.nan)
    ax.plot(az, y, color="#F0B23A", lw=5, solid_capstyle="round", zorder=5)
    ax.set_xlim(90, 270); ax.set_ylim(-2, top)
    ax.set_xticks([90, 135, 180, 225, 270]); ax.set_xticklabels(["E", "SE", "S", "SW", "W"], fontproperties=FELL, fontsize=11)
    ax.set_yticks(range(0, top + 1, 10)); ax.set_yticklabels([f"{v}°" for v in range(0, top + 1, 10)], fontproperties=FELL, fontsize=10)
    for v in range(0, top + 1, 5):
        ax.axhline(v, color="#E2D3AE", lw=0.6, zorder=1)
    for sp in ax.spines.values(): sp.set_color("#BCA676")
    ax.set_facecolor("#FBF5E4")
    sub = (f"no direct sun for {int(s.nodays)} days" if s.nodays else f"{hm(s.sol_min)} of sun on 21 Dec, {hm(s.lost_min)} lost")
    ax.set_title(f"{title}", fontproperties=HAND, fontsize=17, color=RED, loc="left", pad=16)
    ax.text(0, 1.015, sub, transform=ax.transAxes, fontproperties=FELL, fontsize=11.5, color=INKC, va="bottom")


