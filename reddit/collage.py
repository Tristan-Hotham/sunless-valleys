"""Reddit collage (r/dataisbeautiful style): the map of sunshine lost on 21 December, four skylines, the darkest places.
Light parchment background; labels on the sea with a halo; full legend; source footer. Output: reddit/sunless_valleys_collage.png
(2700 x 3300 px). Run after code/06_figures.py."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from sunfig import *

OUT = os.path.join(ROOT, "reddit", "sunless_valleys_collage.png")
fig = plt.figure(figsize=(9, 11), dpi=300); parchment(fig, seed=5, alpha=0.05)

# ---- title
fig.text(0.04, 0.962, "Britain's sunless valleys", fontproperties=HAND, fontsize=34, color=RED, va="center")
fig.text(0.04, 0.927, f"On the shortest day, hills hide the low sun. {R['zero_sol']} UK settlements get no direct sun at all on 21 December.",
         fontproperties=FELL, fontsize=12.2, color=INKC, va="center")
fig.text(0.04, 0.905, "Computed from 90 m terrain for every town, village and hamlet in Wikidata, and every 175 m square of land.",
         fontproperties=FELL, fontsize=10.5, color=MUT, va="center")

# ---- the map
ax = fig.add_axes([0.0, 0.17, 0.60, 0.72])
ext, f = ink_base(ax, 3857, (-10.6, 2.0, 49.85, 59.4), coast_lw=0.5, ripple_m=(6e3, 15e3, 28e3))
import warnings; warnings.simplefilter("ignore")
k = 2
a = lostf; h, w = a.shape[0] // k * k, a.shape[1] // k * k
b = np.nanmax(a[:h, :w].reshape(h // k, k, w // k, k), axis=(1, 3))
x0, y0 = px2m(X0 * 128, Y0 * 128, 9); x1, y1 = px2m(X0 * 128 + w, Y0 * 128 + h, 9)
ax.imshow(lost_rgba(b, 0.95), extent=(x0, x1, y1, y0), zorder=3.5, interpolation="nearest")
z = S[S.sunless].sort_values("nodays")
mx, my = ll2m(z.lon.values, z.lat.values)
ax.scatter(mx, my, s=3 + z.nodays.values * 0.22, c="#1F1838", edgecolors=PAPER, linewidths=0.5, zorder=6)
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_facecolor("none")
# labels on the sea: (name, county, label lon, label lat, ha)
LAB = [("Camas-luinie", "Highland", -9.9, 57.95, "left"), ("Kinlochleven", "Highland", -9.9, 56.75, "left"),
       ("Seldom Seen", "Cumbria", 0.4, 55.15, "left"), ("Penmaenpool", "Gwynedd", -5.6, 53.78, "left"),
       ("Ilkley", "West Yorkshire", 0.35, 54.25, "left"), ("Ferndale", "Mid Glamorgan", -6.6, 51.33, "left")]
for nm, county, lx, ly, ha in LAB:
    r = S[(S["name"] == nm) & (S.county == county)].iloc[0]
    px, py = ll2m(r.lon, r.lat); tx, ty = ll2m(lx, ly)
    sub = f"{int(r.nodays)} days without sun" if r.sunless else f"{hm(r.sol_min)} of sun"
    ax.annotate(f"{nm}\n{sub}", (px, py), xytext=(tx, ty), fontproperties=FELL, fontsize=8.6, color=INKC, ha=ha, va="center", zorder=9,
                path_effects=HALO, arrowprops=dict(arrowstyle="-", color=INKC, lw=0.55, shrinkA=1, shrinkB=2.5))

# ---- legend under the map
lax = fig.add_axes([0.04, 0.085, 0.56, 0.075]); lax.axis("off"); lax.set_xlim(0, 1); lax.set_ylim(0, 1)
lax.text(0, 0.92, "Share of 21 December's sunshine blocked by hills (against a flat horizon)", fontproperties=FELLSC, fontsize=9.5, color=RED, va="center")
labs = ["10 to 25%", "25 to 50%", "50 to 75%", "75 to 99%", "all of it"]
for i, (c, l) in enumerate(zip(LG["lost"]["colours"], labs)):
    x = i * 0.2
    lax.add_patch(plt.Rectangle((x, 0.42), 0.045, 0.26, fc=c, ec=INKC, lw=0.4))
    lax.text(x + 0.055, 0.55, l, fontproperties=FELL, fontsize=8.6, color=INKC, va="center")
lax.scatter([0.022], [0.1], s=26, c="#1F1838", edgecolors=PAPER, linewidths=0.5)
lax.text(0.055, 0.1, "settlement with no direct sun on 21 December (bigger: more sunless days)", fontproperties=FELL, fontsize=8.6, color=INKC, va="center")

# ---- skylines on the right
sky = [("Kinlochleven", "Highland", "Kinlochleven"), ("Seldom Seen", "Cumbria", "Seldom Seen, Cumbria"),
       ("Penmaenpool", "Gwynedd", "Penmaenpool, Gwynedd"), ("Ilkley", "West Yorkshire", "Ilkley, Wharfedale")]
fig.text(0.64, 0.875, "The skyline, and the sun's path", fontproperties=FELLSC, fontsize=11, color=RED)
for i, (n, c, t) in enumerate(sky):
    ax = fig.add_axes([0.67, 0.735 - i * 0.17, 0.30, 0.095])
    skyline(ax, idx(n, c), t, top=30)
    ax.title.set_fontsize(11); ax.title.set_position((0, 1.0))
    for tl in ax.get_xticklabels() + ax.get_yticklabels(): tl.set_fontsize(7.5)
    ax.texts[-1].set_fontsize(8.2)
kx = fig.add_axes([0.64, 0.10, 0.34, 0.055]); kx.axis("off"); kx.set_xlim(0, 1); kx.set_ylim(0, 1)
for j, (col, ls, lw, l) in enumerate(((INKC, "-", 6, "terrain skyline"), (RED, "-", 1.6, "sun on 21 December"),
                                      ("#F0B23A", "-", 4, "where the sun clears the hills"), ("#C77A2A", (0, (4, 3)), 1.1, "sun a month and two months either side"))):
    y = 0.85 - j * 0.25
    kx.plot([0.0, 0.08], [y, y], color=col, ls=ls, lw=lw, solid_capstyle="butt")
    kx.text(0.11, y, l, fontproperties=FELL, fontsize=8.4, color=INKC, va="center")

# ---- footer
fig.text(0.04, 0.032, "Terrain: AWS Terrain Tiles (zoom 10, about 90 m; SRTM). Settlements: Wikidata (CC0). Clear skies; no buildings or trees; "
         f"Wikidata point of each place,\n2 m above ground; a place counts as sunless only if it is also sunless at its OpenStreetMap point ({R['disputed']} of {R['zero_pts']} were not).\n"
         "Sun from declination and latitude with refraction. Dr Tristan Hotham, Independent researcher, 2026.",
         fontproperties=FELL, fontsize=8.2, color=MUT, va="center", linespacing=1.4)
fig.text(0.96, 0.072, "maps.tristanhotham.com/sunless-valleys", fontproperties=FELL, fontsize=10, color=RED, va="center", ha="right")
fig.savefig(OUT, dpi=300, facecolor=fig.get_facecolor()); plt.close(fig)
im = Image.open(OUT); print(OUT, im.size)
assert im.size[0] >= 2400
