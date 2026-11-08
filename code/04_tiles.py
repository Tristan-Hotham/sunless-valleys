"""Step 4: map tiles (256 px palette PNGs, zooms 5 to 9) from the per-cell grid of step 2.
  tiles/lost/{z}/{x}/{y}.png    share of the flat-horizon solstice sunshine blocked by terrain (blank below 10%)
  tiles/hours/{z}/{x}/{y}.png   hours of direct sun on 21 December
  tiles/dark/{z}/{x}/{y}.png    days around the solstice with no direct sun (blank where there are none)
The grid is at zoom-9 pixel size and aligned to zoom-9 pixels. Lower zooms take the maximum (lost, dark) or the mean
(hours) of each 2 x 2 block, so that narrow valleys stay visible on the overview. Empty tiles are not written."""
import shutil
import numpy as np
from PIL import Image
from common import *

sol = np.load(f"{WORK}/sol_min.npy")
nod = np.load(f"{WORK}/nodays.npy")
flat = np.load(f"{WORK}/flat_min_row.npy")[::2][:sol.shape[0]]
land = sol != 65535
solf = np.where(land, sol, np.nan).astype(np.float32)
flatg = np.broadcast_to(flat[:, None], sol.shape)
lostf = np.where(land, np.clip(1 - solf / flatg, 0, 1), np.nan).astype(np.float32)
darkd = np.where(land, nod, 0).astype(np.float32)
np.save(f"{WORK}/lostf.npy", lostf)

# class breaks and colours (index 0 is transparent)
LOST_BR = [0.10, 0.25, 0.50, 0.75, 0.999]
LOST_C = ["#F2C46B", "#E08A3C", "#B5482E", "#6E2547", "#1F1838"]
LOST_A = [150, 185, 215, 235, 245]
HOURS_BR = [0, 1, 60, 120, 180, 240, 300, 360]
HOURS_C = ["#1F1838", "#3B2F5C", "#5C4A78", "#86668E", "#B48A8C", "#D9AE80", "#F0CF7A", "#FBE7A1"]
DARK_BR = [1, 15, 31, 61, 91]
DARK_C = ["#9DB7D5", "#6A8FC0", "#3F63A3", "#2A3F7A", "#141C45"]


def classes(v, br):
    c = np.zeros(v.shape, np.uint8)
    for i, b in enumerate(br):
        c[v >= b] = i + 1
    return c


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def pal_img(cls, cols, alphas):
    im = Image.fromarray(cls, "P")
    pal = [0, 0, 0] + [x for c in cols for x in hexrgb(c)]
    im.putpalette(pal + [0] * (768 - len(pal)))
    im.info["transparency"] = bytes([0] + list(alphas))
    return im


def pyramid(arr, how):
    """arr at zoom 9 -> {z: array}"""
    out = {9: arr}
    a = arr
    for z in range(8, 4, -1):
        h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        b = a[:h, :w].reshape(h // 2, 2, w // 2, 2)
        with np.errstate(all="ignore"):
            import warnings; warnings.simplefilter("ignore")
            a = np.nanmax(b, axis=(1, 3)) if how == "max" else np.nanmean(b, axis=(1, 3))
        out[z] = a
    return out


def write_tiles(name, arr, how, br, cols, alphas):
    d = os.path.join(ROOT, "tiles", name)
    if os.path.exists(d): shutil.rmtree(d)
    n = 0; size = 0
    for z, a in pyramid(arr, how).items():
        k = 2 ** (9 - z)
        gx0, gy0 = X0 * 128 // k, Y0 * 128 // k        # global pixel of the array's corner at this zoom
        cls = classes(np.nan_to_num(a, nan=-1), br)
        tx0, ty0 = gx0 // 256, gy0 // 256
        tx1, ty1 = (gx0 + a.shape[1] - 1) // 256, (gy0 + a.shape[0] - 1) // 256
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                t = np.zeros((256, 256), np.uint8)
                x0, y0 = tx * 256 - gx0, ty * 256 - gy0
                sx0, sy0 = max(0, x0), max(0, y0)
                sx1, sy1 = min(a.shape[1], x0 + 256), min(a.shape[0], y0 + 256)
                if sx1 <= sx0 or sy1 <= sy0: continue
                t[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = cls[sy0:sy1, sx0:sx1]
                if not t.any(): continue
                p = f"{d}/{z}/{tx}/{ty}.png"; os.makedirs(os.path.dirname(p), exist_ok=True)
                pal_img(t, cols, alphas).save(p, optimize=True)
                n += 1; size += os.path.getsize(p)
    print(name, n, "tiles", size // 1024, "KB")


write_tiles("lost", lostf, "max", LOST_BR, LOST_C, LOST_A)
write_tiles("dark", np.where(land, darkd, np.nan), "max", DARK_BR, DARK_C, [210, 225, 235, 245, 250])
write_tiles("hours", solf, "mean", HOURS_BR, HOURS_C, [200] * 8)
jsave({"lost": {"breaks": LOST_BR, "colours": LOST_C}, "hours": {"breaks": HOURS_BR, "colours": HOURS_C},
       "dark": {"breaks": DARK_BR, "colours": DARK_C}}, f"{DATA}/legend.json", indent=1)
