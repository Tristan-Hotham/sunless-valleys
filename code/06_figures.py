"""Step 6: figures for the page (img/), the blog (release/blog/b_*.png), the paper (release/paper/f_*.png) and the header."""
from sunfig import *

BLOG, PAPERD = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (BLOG, PAPERD):
    os.makedirs(d, exist_ok=True)


def out(fig, name, page=True, blog=True, paper=True, dpi=200):
    fig.savefig(f"{WORK}/{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{WORK}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=84, optimize=True)
    if blog:
        w = min(1800, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        w = min(2000, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{PAPERD}/f_{name}.png", optimize=True)
    os.remove(f"{WORK}/{name}.png")


fig = plt.figure(figsize=(9, 12.6)); parchment(fig)
ax = fig.add_axes([0.0, 0.035, 1, 0.885])
overview(ax)
ax.set_facecolor("none")
fig.text(0.04, 0.965, "Where the hills hide the winter sun", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.935, "Share of 21 December's sunshine blocked by terrain, and settlements with no direct sun at all", fontproperties=FELL, fontsize=13, color=MUT, va="center")
lax = fig.add_axes([0.69, 0.60, 0.27, 0.20]); lax.axis("off")
labs = ["10 to 25%", "25 to 50%", "50 to 75%", "75% to almost all", "All of it: no direct sun"]
for i, (c, l) in enumerate(zip(LG["lost"]["colours"], labs)):
    lax.add_patch(plt.Rectangle((0, 1 - (i + 1) * 0.15), 0.12, 0.11, fc=c, ec=INKC, lw=0.5, transform=lax.transAxes))
    lax.text(0.17, 1 - (i + 1) * 0.15 + 0.055, l, fontproperties=FELL, fontsize=12, color=INKC, va="center", transform=lax.transAxes)
lax.scatter([0.06], [0.1], s=60, c="#1F1838", edgecolors=PAPER, transform=lax.transAxes)
lax.text(0.17, 0.1, "Settlement with sunless days\n(bigger: more days)", fontproperties=FELL, fontsize=12, color=INKC, va="center", transform=lax.transAxes)
lax.text(0, 1.04, "Sunshine lost on 21 December", fontproperties=FELLSC, fontsize=13, color=RED, transform=lax.transAxes)
fig.text(0.04, 0.012, "Terrain: AWS Terrain Tiles (90 m). Settlements: Wikidata. Sun lost compared with a flat horizon; clear skies, no buildings or trees.", fontproperties=FELL, fontsize=10, color=MUT)
out(fig, "britain")


sky = [("Kinlochleven", "Highland", "Kinlochleven, Lochaber"), ("Seldom Seen", "Cumbria", "Seldom Seen, Glencoyne"),
       ("Penmaenpool", "Gwynedd", "Penmaenpool, Mawddach"), ("Ilkley", "West Yorkshire", "Ilkley, Wharfedale")]
fig, axs = plt.subplots(2, 2, figsize=(12, 7.6)); parchment(fig)
fig.subplots_adjust(left=0.06, right=0.98, top=0.86, bottom=0.07, hspace=0.42, wspace=0.12)
for ax, (n, c, t) in zip(axs.ravel(), sky):
    skyline(ax, idx(n, c), t)
fig.text(0.06, 0.955, "The skyline from four places, with the winter sun", fontproperties=FELL, fontsize=21, color=INKC)
fig.text(0.06, 0.915, "Black: the terrain horizon. Red: the sun's path on 21 December, gold where it clears the hills. Dashed: 21 Nov or 21 Jan, and 21 Oct or 21 Feb.",
         fontproperties=FELL, fontsize=11.5, color=MUT)
out(fig, "skylines")

# ---------- 3. the calendar of darkness
z = S[S.sunless].sort_values(["nodays", "hor_s"], ascending=False).head(24).iloc[::-1]
fig = plt.figure(figsize=(12, 9)); parchment(fig)
ax = fig.add_axes([0.30, 0.08, 0.66, 0.80])
for j, (_, r) in enumerate(z.iterrows()):
    k = (r.nodays - 1) / 2
    ax.barh(j, r.nodays, left=-k - 0.5, height=0.62, color="#1F1838" if r.nodays >= 61 else "#3F63A3", edgecolor=INKC, lw=0.5)
    ax.text(k + 2, j, f"{int(r.nodays)} days", va="center", fontproperties=FELL, fontsize=11, color=INKC)
ax.set_yticks(range(len(z))); ax.set_yticklabels([f"{r['name']}, {r.county}" for _, r in z.iterrows()], fontproperties=FELL, fontsize=11.5)
ticks = [-61, -51, -40, -30, -20, -10, 0, 11, 21, 31, 42, 52, 62]
lab = []
for t in ticks:
    dd = pd.Timestamp("2026-12-21") + pd.Timedelta(days=t)
    lab.append(f"{dd.day} {dd.strftime('%b')}")
ax.set_xticks(ticks); ax.set_xticklabels(lab, fontproperties=FELL, fontsize=10.5, rotation=0)
ax.axvline(0, color=RED, lw=1.2); ax.text(0, len(z) - 0.2, "21 Dec", color=RED, ha="center", fontproperties=FELL, fontsize=11)
ax.set_xlim(-66, 72)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.set_facecolor("none")
fig.text(0.04, 0.95, "When the sun never reaches them", fontproperties=FELL, fontsize=22, color=INKC)
fig.text(0.04, 0.915, "The settlements with the longest run of days without direct sun, centred on the winter solstice", fontproperties=FELL, fontsize=12.5, color=MUT)
out(fig, "calendar")


# ---------- 4 and 5. zooms with hill shading
dem = np.load(f"{WORK}/dem.npy", mmap_mode="r")
landm = np.load(f"{WORK}/land.npy", mmap_mode="r")


def zoom(ax, lon0, lon1, lat0, lat1, names, label_offsets):
    (X_0, X_1), (Y_1, Y_0) = ll2px(np.array([lon0, lon1]), np.array([lat0, lat1]))
    xa, xb = int(X_0) - X0 * 256, int(X_1) - X0 * 256; ya, yb = int(Y_0) - Y0 * 256, int(Y_1) - Y0 * 256
    sub = np.asarray(dem[ya:yb, xa:xb], float); lm = np.asarray(landm[ya:yb, xa:xb])
    ls = LightSource(azdeg=315, altdeg=40)
    shade = ls.hillshade(np.maximum(sub, 0), vert_exag=1.6, dx=60, dy=60)
    rgb = np.empty(sub.shape + (3,))
    base = np.array([241, 226, 184]) / 255
    for c in range(3):
        rgb[..., c] = np.where(lm, base[c] * (0.55 + 0.5 * shade), np.array([246, 238, 216])[c] / 255)
    ex0, ey0 = px2m(X0 * 256 + xa, Y0 * 256 + ya, 10); ex1, ey1 = px2m(X0 * 256 + xb, Y0 * 256 + yb, 10)
    ax.imshow(np.clip(rgb, 0, 1), extent=(ex0, ex1, ey1, ey0), interpolation="bilinear", zorder=1)
    ax.contour(np.linspace(ex0, ex1, sub.shape[1]), np.linspace(ey0, ey1, sub.shape[0]), lm.astype(float), levels=[0.5], colors=[INKC], linewidths=0.9, zorder=2)
    # the lost layer at grid resolution
    ga, gb, gc, gd = ya // 2, yb // 2, xa // 2, xb // 2
    g = lostf[ga:gb, gc:gd]
    gx0, gy0 = px2m(X0 * 128 + gc, Y0 * 128 + ga, 9); gx1, gy1 = px2m(X0 * 128 + gd, Y0 * 128 + gb, 9)
    ax.imshow(lost_rgba(g, 0.62), extent=(gx0, gx1, gy1, gy0), interpolation="nearest", zorder=3)
    z = S[(S.lon > lon0) & (S.lon < lon1) & (S.lat > lat0) & (S.lat < lat1)]
    mx, my = ll2m(z.lon.values, z.lat.values)
    cols = np.where(z.sunless, "#1F1838", PAPER)
    ax.scatter(mx, my, s=np.where(z.sunless, 46, 16), c=cols, edgecolors=INKC, linewidths=0.8, zorder=6)
    for n, (dx, dy, ha) in label_offsets.items():
        r = z[z["name"] == n]
        if not len(r): print("no label", n); continue
        r = r.iloc[0]; x, y = ll2m(r.lon, r.lat)
        t = f"{n}\n" + (f"{int(r.nodays)} days without sun" if r.sunless else f"{hm(r.sol_min)} of sun")
        ax.annotate(t, (x, y), xytext=(x + dx, y + dy), fontproperties=FELL, fontsize=11.5, color=INKC, ha=ha, va="center", zorder=8, path_effects=HALO,
                    arrowprops=dict(arrowstyle="-", color=INKC, lw=0.7, shrinkA=0, shrinkB=4))
    ax.set_xlim(ex0, ex1); ax.set_ylim(ey1, ey0); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(INKC); sp.set_linewidth(1.2)


fig = plt.figure(figsize=(12, 9.6)); parchment(fig)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.86])
zoom(ax, -5.62, -4.62, 56.58, 56.92, None,
     {"Kinlochleven": (9000, -5200, "left"), "Glencoe": (-3000, -9000, "center"), "Fort William": (9000, 3000, "left"),
      "Achriabhach": (-12000, -5500, "center"), "Ballachulish": (-10000, 3500, "right")})
fig.text(0.03, 0.95, "Lochaber: Glen Coe, Kinlochleven and Glen Nevis", fontproperties=FELL, fontsize=22, color=INKC)
fig.text(0.03, 0.915, "Share of 21 December's sunshine blocked by terrain (colours as on the map of Britain); dark dots: no direct sun on the solstice", fontproperties=FELL, fontsize=12, color=MUT)
out(fig, "lochaber")

fig = plt.figure(figsize=(12, 9.6)); parchment(fig)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.86])
zoom(ax, -3.42, -2.72, 54.36, 54.64, None,
     {"Seldom Seen": (7000, 3500, "left"), "Stonethwaite": (-7000, -3500, "right"), "Keswick": (-6000, 3000, "right"),
      "Glenridding": (7000, -3000, "left"), "Ambleside": (7000, -2000, "left"), "Wasdale Head": (-5000, -3500, "right")})
fig.text(0.03, 0.95, "The Lake District: Borrowdale to Ullswater", fontproperties=FELL, fontsize=22, color=INKC)
fig.text(0.03, 0.915, "Share of 21 December's sunshine blocked by terrain; dark dots: no direct sun on the solstice", fontproperties=FELL, fontsize=12, color=MUT)
out(fig, "lakes")

# ---------- 6. towns
t = pd.DataFrame(R["towns"][:12]).iloc[::-1]
fig = plt.figure(figsize=(12, 7.4)); parchment(fig)
ax = fig.add_axes([0.30, 0.09, 0.66, 0.76])
yy = np.arange(len(t))
ax.barh(yy, t.sol_min / 60, color="#F0CF7A", edgecolor=INKC, lw=0.5, label="Direct sun on 21 December")
ax.barh(yy, t.lost_min / 60, left=t.sol_min / 60, color="#1F1838", edgecolor=INKC, lw=0.5, label="Lost behind hills")
ax.set_yticks(yy); ax.set_yticklabels([f"{r['name']}, {r['county']} ({r['pop']:,})" for _, r in t.iterrows()], fontproperties=FELL, fontsize=11.5)
ax.set_xlabel("Hours on 21 December", fontproperties=FELL, fontsize=12)
ax.set_xlim(0, 8.3)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
leg = ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2, prop=FELL, frameon=False, fontsize=11)
fig.text(0.04, 0.94, "Towns that lose the most winter sun", fontproperties=FELL, fontsize=22, color=INKC)
fig.text(0.04, 0.90, "Settlements of 2,000 people or more (Wikidata population), ranked by minutes of solstice sun lost to hills (Penmaenmawr left out: its result depends on the point, see text)", fontproperties=FELL, fontsize=12, color=MUT)
out(fig, "towns")

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100); parchment(fig)
ax = fig.add_axes([0.53, 0.0, 0.47, 1.0])
ext = overview(ax, k=4, dots=True)
ax.set_xlim(*ll2m(np.array([-8.4, 1.9]), np.array([54, 54]))[0]); ax.set_ylim(*ll2m(np.array([0, 0]), np.array([50.0, 58.8]))[1])
kl = R["by_name"]["kinlochleven"]
fig.text(0.04, 0.80, "Britain's", fontproperties=FELL, fontsize=40, color=INKC)
fig.text(0.04, 0.66, "sunless valleys", fontproperties=HAND, fontsize=50, color=RED)
fig.text(0.04, 0.53, f"{R['zero_sol']} settlements get no direct sun\non the shortest day. Kinlochleven\ngoes {kl['nodays']} days without it.",
         fontproperties=FELL, fontsize=18, color=INKC, linespacing=1.35, va="top")
fig.text(0.04, 0.06, "maps.tristanhotham.com/sunless-valleys", fontproperties=FELL, fontsize=13, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
