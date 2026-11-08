"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24055580, https://doi.org/10.5281/zenodo.24055580 and https://blog.tristanhotham.com/2026/10/31/sunless-valleys/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "07_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Sunless_Valleys"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# facts written in words in the blog only
assert R["top"][0]["county"] == "Highland" and R["top"][0]["nodays"] > 90               # "more than three months"
assert R["flat_south_name"] and R["flat_north_name"]
kl = R["by_name"]["kinlochleven"]
assert round(kl["hor_s"]) > round(kl["noon_alt"])

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Britain's sunless valleys",
        "slug": "sunless-valleys",
        "excerpt": f"On the shortest day the sun barely clears the horizon, and hills hide it. I drew the winter sun across the skyline of every town and village in the UK: {R['zero_sol']} get no direct sun at all on 21 December, and Kinlochleven goes {kl['nodays']} days without it.",
        "seo_description": f"Which places in Britain get no winter sun? From 90 m terrain, {R['zero_sol']} UK settlements see no direct sun on 21 December.",
        "tags": ["maps", "data visualisation", "winter solstice", "sunlight", "terrain", "Scotland", "Wales", "Lake District", "geography"],
        "header_alt": f"Title card on parchment reading 'Britain's sunless valleys' in black and red lettering beside a map of Britain shaded amber to violet where hills block the winter sun, with the line {R['zero_sol']} settlements get no direct sun on the shortest day."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/sunless-valleys_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dd in ("code", "js"):
        for fn in sorted(os.listdir(os.path.join(ROOT, dd))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, dd, fn), f"sunless-valleys/{dd}/{fn}")
    for fn in sorted(os.listdir(os.path.join(ROOT, "data"))):
        p = os.path.join(ROOT, "data", fn)
        if os.path.isfile(p):
            z.write(p, f"sunless-valleys/data/{fn}")
    for fn in sorted(os.listdir(os.path.join(ROOT, "data", "prof"))):
        z.write(os.path.join(ROOT, "data", "prof", fn), f"sunless-valleys/data/prof/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"sunless-valleys/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "sunless-valleys/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("km$^2$", "km²").replace("\\textdegree{}", "°")
assert "\\" not in ab and "$" not in ab, ab
zmeta = {"title": "Britain's Sunless Valleys: Where Terrain Hides the Winter Sun",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive page: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/sunless-valleys/}}.</p><p>Sources: AWS Terrain Tiles (Terrarium, zoom 10; chiefly SRTM in Britain and Ireland), Wikidata settlements (CC0), Natural Earth (public domain), ONS boundaries (OGL v3.0). Derived data CC BY 4.0, code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["winter solstice", "terrain horizon", "topographic shading", "insolation", "digital elevation model", "SRTM", "settlements", "Scotland", "Wales", "Lake District"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "Text, figures and derived data CC BY 4.0; code MIT. Terrain from the AWS Terrain Tiles (open data); settlements from Wikidata (CC0).",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": TERRAIN_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in sj, bad
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
