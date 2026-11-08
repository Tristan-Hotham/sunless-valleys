"""Step 8: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Sunless_Valleys.pdf and .tex beside the f_*.png figures. The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Sunless_Valleys"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
names = {t["name"] for t in R["top"][:12]}
assert {"Morvich", "Camas-luinie", "Kinlochleven", "Seldom Seen"} <= names, names
assert not [p for p in R["towns"] if p["sol_min"] == 0]                                     # Penmaenmawr left out of the towns
assert R["by_name"]["newburgh"]["sol_min"] > 0


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "hm": return hm(v)
    return tex(str(v))


rows = ""
for n in ("England", "Scotland", "Wales", "Northern Ireland"):
    x = R["nations"][n]
    rows += f"{n} & {x['n']:,} & {x['median_lost_min']:.0f} & {x['median_share_pc']:.0f}\\% & {x['lost_hour_pc']:.0f}\\% & {x['zero']}\\\\\n"
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{Settlements by nation: number, median minutes and share of the flat-horizon solstice sunshine lost to terrain, "
      "share losing an hour or more, and number with no direct sun on 21 December (after the check of Section~\\ref{sec:check}).}\\label{tab:nations}"
      "\\begin{tabular}{lrrrrr}\\toprule Nation & Settlements & Median lost (min) & Median share & 1 h or more & No sun\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
sh = lambda d: d.split()[0] + " " + d.split()[1][:3]
rows = ""
for p in R["top"][:15]:
    rows += (f"{tex(p['name'])} & {tex(p['county'])} & {p['elev_m']} & {p['hor_s']:.1f} & {p['noon_alt']:.1f} & {p['nodays']} & {sh(p['from'])} to {sh(p['to'])}\\\\\n")
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The settlements with the longest runs of days without direct sun: ground height (m), horizon due south and "
      "noon solar altitude on 21 December (degrees), and the run of sunless days.}\\label{tab:top}"
      "\\begin{tabular}{llrrrrl}\\toprule Settlement & County & Height & South horizon & Noon sun & Days & Dates\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for n in ("England", "Scotland", "Wales", "Northern Ireland", "United Kingdom", "Ireland", "Isle of Man"):
    g = R["grid"][n]
    rows += f"{n} & {g['land_km2']:,.0f} & {g['zero_km2']:,.1f} & {g['dark30_km2']:,.1f} & {g['dark60_km2']:,.1f} & {g['half_pc']:.1f}\\%\\\\\n"
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Land in terrain shadow, from the grid: land area, area with no direct sun on 21 December, with none for at "
      "least 30 and at least 61 days, and share of land losing half or more of the solstice sunshine (km$^2$). United Kingdom includes coastal cells outside "
      "the county outlines.}\\label{tab:grid}"
      "\\begin{tabular}{lrrrrr}\\toprule Area & Land & No sun 21 Dec & 30+ days & 61+ days & Half lost\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{TABLE_NATIONS}}", TN).replace("{{TABLE_TOP}}", TT).replace("{{TABLE_GRID}}", TG)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")          # the publisher sets DOI=10.5281/zenodo.N and reruns this step
t = t.replace("https://doi.org/10.5281/zenodo.24055580", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
