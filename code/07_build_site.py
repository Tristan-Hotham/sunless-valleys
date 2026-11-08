"""Step 7: index.html from code/page_template.html and data/results.json, with the facts written in words checked.
10.5281/zenodo.24055580, https://doi.org/10.5281/zenodo.24055580 and https://blog.tristanhotham.com/2026/10/31/sunless-valleys/ stay as placeholders for the publisher."""
import re, time
from common import *

R = jload(f"{DATA}/results.json")
LG = jload(f"{DATA}/legend.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# ---- facts stated in words (page, blog, paper)
kl, ss, pm = R["by_name"]["kinlochleven"], R["by_name"]["seldom_seen"], R["by_name"]["penmaenmawr"]
assert kl["hor_s"] > kl["noon_alt"] and kl["pop"] == max(p["pop"] for p in R["zero_with_pop"] if p["nation"] == "Scotland")
assert kl["pop"] == max(p["pop"] for p in R["zero_with_pop"])                           # Kinlochleven "is the largest"
assert R["point_check"]["by_qid"]["Q2653611"]["osm_sol_min"] > 0                      # Penmaenmawr: "not counted"
assert ss["nodays"] > 60 and R["by_name"]["stonethwaite"]["nodays"] > 30
assert R["nations"]["Scotland"]["median_lost_min"] > R["nations"]["England"]["median_lost_min"]
assert R["nations"]["Wales"]["median_lost_min"] > R["nations"]["England"]["median_lost_min"]
assert R["big"][0]["name"] == "Ilkley"
assert R["by_name"]["ferndale"]["county"] == "Mid Glamorgan"
assert R["median_lost_min"] < 30                                                         # "mostly the first and last light"
G = R["grid"]
assert G["Scotland"]["zero_km2"] > 0.8 * G["United Kingdom"]["zero_km2"]


def key_rows(br, cols, labs):
    return "".join(f'<div class="row"><i style="background:{c}"></i>{l}</div>' for c, l in zip(cols, labs))


KL = key_rows(LG["lost"]["breaks"], LG["lost"]["colours"], ["10 to 25%", "25 to 50%", "50 to 75%", "75% to almost all", "all: no direct sun"])
KH = key_rows(None, LG["hours"]["colours"], ["none", "under 1 h", "1 to 2 h", "2 to 3 h", "3 to 4 h", "4 to 5 h", "5 to 6 h", "6 h and more"])
KD = key_rows(LG["dark"]["breaks"], LG["dark"]["colours"], ["1 to 14 days", "15 to 30", "31 to 60", "61 to 90", "91 or more"])
assert len(LG["hours"]["colours"]) == 8
top = "".join(f'<li><a data-go="{p["qid"]}" href="?place={p["qid"]}">{p["name"]}</a>, {p["county"]}: {p["nodays"]} days, {p["from"]} to {p["to"]}</li>'
              for p in R["top"][:12])

t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
fs = open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read()
t = t.replace("{{KEY_LOST}}", KL).replace("{{KEY_HOURS}}", KH).replace("{{KEY_DARK}}", KD).replace("{{LIST_TOP}}", top).replace("{{FULLSCREEN}}", fs)
t = t.replace("{{BYLINE}}", BYLINE).replace("{{AI}}", AI).replace("{{VERSION}}", time.strftime("%Y%m%d"))
t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
js = open(os.path.join(ROOT, "js", "page.js"), encoding="utf-8").read()
assert "—" not in js and "–" not in js
print("index.html", len(t) // 1024, "KB")
