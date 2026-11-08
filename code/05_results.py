"""Step 5: every number quoted anywhere, into data/results.json, with the checks behind the words.
Also writes data/nation_grid_summary.csv (areas by nation) and data/sunless_places.csv (settlements with no direct sun
on 21 December)."""
import csv
import numpy as np
import pandas as pd
from shapely.geometry import shape
from shapely.ops import transform as stransform
from rasterio.features import rasterize
from rasterio.transform import Affine
from common import *

d = pd.read_csv(f"{DATA}/settlements_sun.csv")
d["share"] = d.lost_min / d.flat_min
# The check of code/11_point_check.py (run it once after this step, then run this step again): a settlement counts as
# sunless only if it is sunless at its Wikidata point and, where OpenStreetMap has a place point of the same name nearby,
# also sunless there. "disputed" = sunless at the Wikidata point but not at the OSM point.
PCF = f"{DATA}/point_check.csv"
PC = pd.read_csv(PCF) if os.path.exists(PCF) else None
d["point_check"] = ""
if PC is not None:
    pc = PC.set_index("qid")
    for q, r in pc.iterrows():
        st = "unmatched" if pd.isna(r.osm_offset_km) else ("confirmed" if r.osm_sol_min == 0 else "disputed")
        d.loc[d.qid == q, "point_check"] = st
    assert set(pc.index) == set(d.qid[d.sol_min == 0]), "point_check.csv is out of date: rerun code/11_point_check.py"
dz = d[(d.sol_min == 0) & (d.point_check != "disputed")]          # the sunless settlements that survive the check
R = {}
N = len(d)
R["n_sett"] = N
M = jload(f"{WORK}/dem_meta.json"); R["TILES"] = f"{M['tiles']:,}"; R["despiked"] = M["despiked"]
R["raw_rows"] = sum(1 for _ in open(SETT, encoding="utf-8")) - 1
R["n_named_pop"] = int(d["pop"].notna().sum())
R["zero_pts"] = int((d.sol_min == 0).sum())                # Wikidata points with no sun on the solstice
assert R["zero_pts"] == int((d.nodays > 0).sum())        # no sun on the solstice <=> at least one sunless day
R["zero_sol"] = len(dz)
R["disputed"] = int((d.point_check == "disputed").sum())
for k in (30, 60, 90):
    R[f"dark{k}"] = int((dz.nodays >= k).sum())
R["lost_hour"] = int((d.lost_min >= 60).sum()); R["lost_hour_pc"] = 100 * R["lost_hour"] / N
R["lost_half"] = int((d.share >= 0.5).sum())
R["median_lost_min"] = float(d.lost_min.median())
R["flat_min_south"] = float(d.flat_min.max()); R["flat_min_north"] = float(d.flat_min.min())
R["flat_south_name"] = d.loc[d.flat_min.idxmax(), "name"]; R["flat_north_name"] = d.loc[d.flat_min.idxmin(), "name"]

nat = {}
for n, g in d.groupby("nation"):
    zg = int(((g.sol_min == 0) & (g.point_check != "disputed")).sum())
    nat[n] = {"n": len(g), "zero": zg, "zero_pc": 100 * zg / len(g), "zero_pts": int((g.sol_min == 0).sum()), "median_lost_min": float(g.lost_min.median()),
              "median_share_pc": 100 * float(g.share.median()), "lost_hour_pc": 100 * float((g.lost_min >= 60).mean())}
R["nations"] = nat


def span(nd):
    k = (nd - 1) // 2
    a = pd.Timestamp("2026-12-21") - pd.Timedelta(days=k); b = pd.Timestamp("2026-12-21") + pd.Timedelta(days=k)
    return f"{a.day} {a.strftime('%B')}", f"{b.day} {b.strftime('%B')}"


def rec(r):
    o = {"qid": r.qid, "name": r["name"], "county": r.county, "nation": r.nation, "pop": None if pd.isna(r["pop"]) else int(r["pop"]),
         "elev_m": int(r.elev_m), "sol_min": float(r.sol_min), "flat_min": float(r.flat_min), "lost_min": float(r.lost_min),
         "share_pc": 100 * float(r.share), "nodays": int(r.nodays), "hor_s": float(r.hor_s), "hor_max": float(r.hor_max), "noon_alt": float(r.noon_alt),
         "lat": float(r.lat), "lon": float(r.lon)}
    if r.nodays > 0:
        o["from"], o["to"] = span(int(r.nodays))
    return o


top = dz.sort_values(["nodays", "hor_s"], ascending=False)
R["top"] = [rec(r) for _, r in top.head(15).iterrows()]
R["by_name"] = {}
for key, nm, county in (("kinlochleven", "Kinlochleven", "Highland"), ("seldom_seen", "Seldom Seen", "Cumbria"), ("glencoe", "Glencoe", "Highland"),
                        ("penmaenmawr", "Penmaenmawr", "Clwyd"), ("ilkley", "Ilkley", "West Yorkshire"), ("stonethwaite", "Stonethwaite", "Cumbria"),
                        ("morvich", "Morvich", "Highland"), ("camas_luinie", "Camas-luinie", "Highland"), ("newburgh", "Newburgh", "Fife"),
                        ("ferndale", "Ferndale", "Mid Glamorgan"), ("fort_william", "Fort William", "Highland"), ("keswick", "Keswick", "Cumbria"),
                        ("hebden_bridge", "Hebden Bridge", "West Yorkshire"), ("cwm_llech", "Cwm Llech", "Powys"), ("braemar", "Braemar", "Aberdeenshire")):
    m = d[(d["name"] == nm) & (d.county == county)]
    if len(m):
        R["by_name"][key] = rec(m.iloc[0])
    else:
        print("not found", nm)
towns = d[d["pop"] >= 2000].sort_values("lost_min", ascending=False)
R["towns"] = [rec(r) for _, r in towns[towns.point_check != "disputed"].head(12).iterrows()]     # Penmaenmawr: see the text
R["n_towns2000"] = len(towns)
R["towns_lost_2h"] = int((towns.lost_min >= 120).sum())
big = d[d["pop"] >= 10000].sort_values("lost_min", ascending=False)
R["big"] = [rec(r) for _, r in big.head(5).iterrows()]
R["n_big"] = len(big)
R["zero_with_pop"] = [rec(r) for _, r in dz[dz["pop"].notna()].sort_values("pop", ascending=False).iterrows()]

# ---- the grid: areas by nation (UK nations from the county outlines; Ireland and the Isle of Man from Natural Earth)
sol = np.load(f"{WORK}/sol_min.npy"); nod = np.load(f"{WORK}/nodays.npy")
lostf = np.load(f"{WORK}/lostf.npy")
ny, nx = sol.shape
land = sol != 65535
ox, oy = X0 * 128, Y0 * 128
def to_px(x, y, z=None):
    X, Y = ll2px(x, y)
    return np.asarray(X) / 2 - ox, np.asarray(Y) / 2 - oy
feats = jload(f"{GEO}/counties_uk.geojson")["features"]
NAT = ["England", "Scotland", "Wales", "Northern Ireland"]
reg = np.zeros((ny, nx), np.uint8)
for i, n in enumerate(NAT):
    gs = [stransform(to_px, shape(f["geometry"])) for f in feats if f["properties"]["nation"] == n]
    m = rasterize([(g, 1) for g in gs], out_shape=(ny, nx), transform=Affine.identity(), dtype="uint8")
    reg[(m > 0) & (reg == 0)] = i + 1
country = np.load(f"{WORK}/country.npy")[::2, ::2][:ny, :nx]
reg[(reg == 0) & (country == 1)] = 9          # UK land outside the county outlines (coast slivers): nearest is unknown
reg[country == 2] = 5; reg[country == 3] = 6
NAMES = {1: "England", 2: "Scotland", 3: "Wales", 4: "Northern Ireland", 5: "Ireland", 6: "Isle of Man", 9: "UK coast cells"}
ys = np.arange(ny) * 2 + Y0 * 256 + 1.0
_, lat = px2ll(np.zeros(ny), ys)
cell_km2 = ((2 * PIX0 * np.cos(np.radians(lat))) / 1000) ** 2
A = np.broadcast_to(cell_km2[:, None], (ny, nx))
G = {}
for c, nm in NAMES.items():
    m = land & (reg == c)
    if not m.any(): continue
    G[nm] = {"land_km2": float(A[m].sum()), "zero_km2": float(A[m & (sol == 0)].sum()),
             "dark30_km2": float(A[m & (nod >= 30) & (nod != 255)].sum()), "dark60_km2": float(A[m & (nod >= 61) & (nod != 255)].sum()),
             "dark181_km2": float(A[m & (nod == 181)].sum()),
             "half_km2": float(A[m & (lostf >= 0.5)].sum()), "lost10_km2": float(A[m & (lostf >= 0.1)].sum())}
    G[nm]["zero_pc"] = 100 * G[nm]["zero_km2"] / G[nm]["land_km2"]
    G[nm]["half_pc"] = 100 * G[nm]["half_km2"] / G[nm]["land_km2"]
uk = [G[n] for n in ("England", "Scotland", "Wales", "Northern Ireland", "UK coast cells") if n in G]
G["United Kingdom"] = {k: sum(g[k] for g in uk) for k in ("land_km2", "zero_km2", "dark30_km2", "dark60_km2", "dark181_km2", "half_km2", "lost10_km2")}
G["United Kingdom"]["zero_pc"] = 100 * G["United Kingdom"]["zero_km2"] / G["United Kingdom"]["land_km2"]
G["United Kingdom"]["half_pc"] = 100 * G["United Kingdom"]["half_km2"] / G["United Kingdom"]["land_km2"]
R["grid"] = G
# Ireland by county (Natural Earth admin 1)
irl = []
for f in jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]:
    if f["properties"]["adm0_a3"] != "IRL": continue
    m = rasterize([(stransform(to_px, shape(f["geometry"])), 1)], out_shape=(ny, nx), transform=Affine.identity(), dtype="uint8")
    irl.append({"county": f["properties"]["name"], "zero_km2": float(A[(m > 0) & land & (sol == 0)].sum())})
irl.sort(key=lambda r: -r["zero_km2"])
R["ireland_counties"] = irl[:6]
R["ireland_top4_pc"] = 100 * sum(r["zero_km2"] for r in irl[:4]) / sum(r["zero_km2"] for r in irl)
R["grid_cells"] = int(land.sum())
R["grid_cell_m"] = float(2 * PIX0 * np.cos(np.radians(55)))
with open(f"{DATA}/nation_grid_summary.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["area", "land_km2", "no_sun_21dec_km2", "no_sun_30plus_days_km2", "no_sun_61plus_days_km2", "half_or_more_lost_km2"])
    for nm, g in G.items():
        w.writerow([nm, round(g["land_km2"]), round(g["zero_km2"], 1), round(g["dark30_km2"], 1), round(g["dark60_km2"], 1), round(g["half_km2"])])
sp = d[d.sol_min == 0].sort_values("nodays", ascending=False).drop(columns=["share"])
if PC is not None:
    sp = sp.merge(PC[["qid", "check_sol_min", "check_nodays", "osm_offset_km", "osm_lat", "osm_lon", "osm_sol_min", "osm_nodays"]], on="qid", how="left")
sp.to_csv(f"{DATA}/sunless_places.csv", index=False)
d.drop(columns=["share"]).to_csv(f"{DATA}/settlements_sun.csv", index=False)
if PC is not None:
    m = PC[PC.osm_offset_km.notna()]
    R["point_check"] = {"n": len(PC), "check_zero": int((PC.check_sol_min == 0).sum()),
                        "check_days_median_diff": float((PC.check_nodays - PC.nodays).median()),
                        "check_days_mad": float((PC.check_nodays - PC.nodays).abs().median()),
                        "osm_matched": len(m), "osm_zero": int((m.osm_sol_min == 0).sum()), "osm_sunny": int((m.osm_sol_min > 0).sum()),
                        "unmatched": int(PC.osm_offset_km.isna().sum()), "osm_offset_median_km": float(m.osm_offset_km.median()),
                        "coarse_2dp": int((PC.wd_decimals <= 2).sum()),
                        "osm_sunny_names": list(m[m.osm_sol_min > 0].name),
                        "by_qid": {r.qid: {"osm_offset_km": None if pd.isna(r.osm_offset_km) else float(r.osm_offset_km),
                                           "osm_sol_min": None if pd.isna(r.osm_sol_min) else float(r.osm_sol_min),
                                           "osm_nodays": None if pd.isna(r.osm_nodays) else int(r.osm_nodays)} for r in PC.itertuples()}}

# the sun itself
lat56 = 56.0
R["noon_alt_56"] = 90 - lat56 - 23.44
R["noon_alt_50"] = 90 - 50 - 23.44
R["noon_alt_60"] = 90 - 60 - 23.44

# checks behind words
kl = R["by_name"]["kinlochleven"]
assert kl["sol_min"] == 0 and kl["nodays"] >= 100                          # "more than a hundred days"
assert R["top"][0]["nation"] == "Scotland"
assert R["by_name"]["penmaenmawr"]["sol_min"] == 0 and R["by_name"]["penmaenmawr"]["pop"] > 4000
assert PC is None or d.loc[d["name"] == "Penmaenmawr", "point_check"].iloc[0] == "disputed"
assert R["nations"]["Scotland"]["zero"] > R["nations"]["Wales"]["zero"] > R["nations"]["England"]["zero"]
assert [r["county"] for r in R["ireland_counties"][:4]] == ["Kerry", "Mayo", "Donegal", "Galway"]
assert R["flat_south_name"] == "Old Town" and R["flat_north_name"] == "Valsgarth"
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: v for k, v in R.items() if k not in ("top", "towns", "by_name", "zero_with_pop", "big")}, indent=1)[:3000])
print([(t["name"], t["nodays"], t["from"], t["to"]) for t in R["top"]])
print([(t["name"], t["pop"], round(t["lost_min"])) for t in R["towns"]])
print([(t["name"], t["pop"], t["nodays"]) for t in R["zero_with_pop"]])
print({k: (v["sol_min"], v["nodays"], round(v["lost_min"])) for k, v in R["by_name"].items()})
