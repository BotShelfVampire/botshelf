#!/usr/bin/env python3
"""Build the BSV field pages: /fields/ (hub) and /fields/{healthcare,space,biotech,quantum}/.

Content: scripts/site/fields_content.py (BSV-original recipes, comparison rows, starter-stack summaries).
Evidence read at build time, never typed in:
  fields/test_runs.json     smoke_fields_recipes.py results -> "Tested by BSV" badge + the real output tail
  fields/sources_check.json check_fields_sources.py results -> only HTTP 200 sources are published
Code shipped for download is BSV's own (fields/code/<field>/*.py, MIT). No third-party code is copied.
Writes /fields/index.json with the counts build_home_value.py uses for the homepage tiles.
usage: build_fields.py --site <site>"""
import argparse, datetime as dt, hashlib, html, json, re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fields_content as C

REPO = Path(__file__).resolve().parents[2]
ORIGIN = "https://botshelfvampire.com"
ORDER = ("healthcare", "space", "biotech", "quantum")
L5 = C.LANGS


def esc(s):
    return html.escape(str(s), quote=True)


def md(s):
    """escape, then `code` -> <code>"""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))


def both(en, ja, tag="p", cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-lang-show="en">{en}</{tag}><{tag}{c} data-lang-show="ja" hidden>{ja}</{tag}>'


def t5(key, en, tag="span", cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-i18n="{key}">{esc(en)}</{tag}>'


def shell(site: Path):
    a = (site / "about.html").read_text()
    head_end = a.index("</head>")
    header = a[a.index("<header>"):a.index("</header>") + len("</header>")]
    footer = a[a.index("<footer>"):a.index("</footer>") + len("</footer>")]
    css = re.search(r'<link rel="stylesheet" href="(/css/shelf[^"]+)">', a[:head_end]).group(1)
    scripts = re.findall(r'<script src="([^"]+)" defer></script>', a[a.index("</footer>"):])
    return header, footer, css, scripts


CSS = """.fld h1{font-size:clamp(30px,5vw,48px);line-height:1.1}
.fld [hidden]{display:none!important}
.fld-crumbs{font-size:13px;color:var(--muted);margin:0 0 14px}
.fld-crumbs a{color:var(--muted)}
.fld-lead{font-size:18px;max-width:780px}
.fld-notice{border:1px solid var(--warn-line);background:var(--warn-bg);border-radius:12px;padding:12px 16px;margin:16px 0;max-width:780px}
.fld-toc{display:flex;flex-wrap:wrap;gap:8px 18px;margin:18px 0 28px;padding:0;list-style:none}
.fld-toc a{color:var(--gold);text-decoration:underline;text-underline-offset:3px}
.fld section{margin:0 0 40px}
.fld h2{margin-top:8px}
.fld-sublead{color:var(--muted);max-width:780px}
.fld-recipe{border:1px solid var(--line);border-radius:14px;background:var(--card);padding:18px 20px;margin:0 0 18px}
.fld-recipe h3{margin:0 0 6px;font-size:20px;line-height:1.3}
.fld-badge{display:inline-block;font-size:12px;letter-spacing:.04em;border-radius:999px;padding:2px 10px;margin:0 0 8px}
.fld-badge-ok{border:1px solid var(--ok-line);background:var(--ok-bg);color:var(--gold)}
.fld-badge-no{border:1px solid var(--warn-line);background:var(--warn-bg);color:var(--muted)}
.fld-dl{margin:12px 0}
.fld-dl dt{color:var(--gold);font-weight:650;margin-top:10px}
.fld-dl dd{margin:2px 0 0}
.fld-dl ol{margin:4px 0 0;padding-left:22px}
.fld-dl li{margin:0 0 4px}
.fld code{font-size:.92em;background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:0 4px;overflow-wrap:anywhere}
.fld pre{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;max-height:440px;font-size:13px;line-height:1.45;margin:8px 0}
.fld pre code{border:0;padding:0;background:none}
.fld details{margin:10px 0 0}
.fld-run{font-size:13px;color:var(--muted)}
.fld-tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}
.fld table{border-collapse:collapse;width:100%;min-width:680px;font-size:14px}
.fld th,.fld td{border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
.fld th{color:var(--gold);font-weight:650;background:var(--card)}
.fld-stack{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px;list-style:none;padding:0;margin:0}
.fld-stack li{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:14px 16px}
.fld-stack h3{font-size:16px;margin:0 0 4px}
.fld-meta{font-size:13px;color:var(--muted);margin:4px 0}
.fld-cats{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;list-style:none;padding:0}
.fld-cats a{display:block;border:1px solid var(--line);border-radius:14px;background:var(--card);padding:18px;color:var(--ink);height:100%;box-sizing:border-box}
.fld-cats strong{color:var(--gold);font-size:18px;display:block;margin:0 0 6px}
.fld-related{padding-left:20px}
.fld-lab{border:1px solid var(--ok-line);background:var(--ok-bg);border-radius:12px;padding:12px 16px;margin:16px 0;max-width:780px}
.fld-lab a{font-weight:650;font-size:17px}
"""


def page_i18n():
    d = {l: {} for l in L5}
    for k, v in C.UI.items():
        for i, l in enumerate(L5):
            d[l][k] = v[i]
    for cat, f in C.F.items():
        for i, l in enumerate(L5):
            d[l][f"fld_{cat}_name"] = f["name"][i]
            d[l][f"fld_{cat}_h1"] = f["h1"][i]
            d[l][f"fld_{cat}_lead"] = f["lead"][i]
            d[l][f"fld_{cat}_title"] = f"{f['name'][i]} | BotShelf Vampire"
            if f.get("notice"):
                d[l][f"fld_{cat}_notice"] = f["notice"][i]
            for r in f["recipes"]:
                d[l][f"fld_{cat}_{r['id']}_t"] = r["title"][i]
                d[l][f"fld_{cat}_{r['id']}_s"] = r["summary"][i]
    for i, l in enumerate(L5):
        d[l]["fld_hub_title"] = f"{C.UI['fldHubTitle'][i]} | BotShelf Vampire"
    return d


def assets(site: Path):
    out = site / "fields"
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("fields.*.css"):
        p.unlink()
    for p in out.glob("fields-i18n.*.js"):
        p.unlink()
    js = "/* BSV field pages: strings for i18n.v20260909brand.js (generated by build_fields.py) */\nwindow.PAGE_I18N=" + json.dumps(page_i18n(), ensure_ascii=False, separators=(",", ":")) + ";\n"
    hc = hashlib.sha1(CSS.encode()).hexdigest()[:8]
    hj = hashlib.sha1(js.encode()).hexdigest()[:8]
    (out / f"fields.{hc}.css").write_text(CSS)
    (out / f"fields-i18n.{hj}.js").write_text(js)
    return f"/fields/fields.{hc}.css", f"/fields/fields-i18n.{hj}.js"


def doc(site, rel_url, title_key, title_en, desc, crumbs, body, css_href, js_href):
    header, footer, shelf_css, scripts = shell(site)
    url = ORIGIN + rel_url
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": ORIGIN + u} for i, (u, n) in enumerate(crumbs)]}
    scr = "".join(f'<script src="{s}" defer></script>\n' for s in [js_href] + scripts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#000000">
<meta name="format-detection" content="telephone=no">
<title data-i18n="{title_key}">{esc(title_en)} | BotShelf Vampire</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="BotShelf Vampire">
<meta property="og:title" content="{esc(title_en)} | BotShelf Vampire">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://botshelfvampire.com/img/hero.webp">
<link rel="icon" href="/img/mark.jpg" type="image/jpeg">
<link rel="stylesheet" href="{shelf_css}">
<link rel="stylesheet" href="{css_href}">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}
</script>
</head>
<body>
{header}
<main class="wrap fld">
{body}
</main>

{footer}
{scr}</body>
</html>
"""


def crumbs_html(items):
    parts = []
    for href, key, en in items:
        parts.append(f'<a href="{href}" data-i18n="{key}">{esc(en)}</a>' if href else f'<span data-i18n="{key}">{esc(en)}</span>')
    return '<nav class="fld-crumbs" aria-label="Breadcrumb"><a href="/">BotShelf Vampire</a> › ' + " › ".join(parts) + "</nav>"


IMPORTS = {"mujoco": "mujoco", "pydicom": "pydicom", "rdkit": "rdkit", "Bio": "biopython", "skyfield": "skyfield",
           "pystac_client": "pystac-client", "qiskit": "qiskit", "qiskit_aer": "qiskit-aer", "pennylane": "pennylane", "numpy": "numpy"}


def recipe_versions(src, tr):
    """'Python x, pkg ver, ...' for the packages this script actually imports (versions recorded by the smoke run)."""
    mods = set(re.findall(r"^\s*(?:from|import)\s+([A-Za-z_]+)", src, re.M))
    pk = [IMPORTS[m] for m in IMPORTS if m in mods]
    return ", ".join([tr.get("python", "Python")] + [f"{k} {tr['versions'][k]}" for k in pk if k in tr.get("versions", {})])


def recipe_html(cat, r, runs, versions):
    rid, U = r["id"], C.UI
    run = runs.get(r.get("code") or "")
    tested = bool(run and run.get("ok") and run.get("files_ok"))
    o = [f'<article class="fld-recipe" id="{rid}">',
         f'<h3 data-i18n="fld_{cat}_{rid}_t">{esc(r["title"][0])}</h3>',
         (f'<span class="fld-badge fld-badge-ok" data-i18n="fldTested">{esc(U["fldTested"][0])}</span>' if tested else
          f'<span class="fld-badge fld-badge-no" data-i18n="fldUntested">{esc(U["fldUntested"][0])}</span>'),
         f'<p data-i18n="fld_{cat}_{rid}_s">{esc(r["summary"][0])}</p>', '<dl class="fld-dl">']
    for key, fld in (("fldInput", "input"), ("fldOutput", "output"), ("fldPrereq", "prereq")):
        o.append(f'<dt data-i18n="{key}">{esc(U[key][0])}</dt><dd>{both(md(r[fld][0]), md(r[fld][1]), "span")}</dd>')
    o.append(f'<dt data-i18n="fldSteps">{esc(U["fldSteps"][0])}</dt><dd>')
    for lang, hid in (("en", ""), ("ja", " hidden")):
        o.append(f'<ol data-lang-show="{lang}"{hid}>' + "".join(f"<li>{md(s)}</li>" for s in r["steps"][lang]) + "</ol>")
    o.append("</dd>")
    o.append(f'<dt data-i18n="fldExpected">{esc(U["fldExpected"][0])}</dt><dd>{both(md(r["expected"][0]), md(r["expected"][1]), "span")}</dd>')
    nh = r.get("next_href")
    ext = ' rel="noopener" target="_blank"' if nh and nh.startswith("http") else ""
    link = f' <a href="{esc(nh)}"{ext} data-i18n="fldOpen">{esc(U["fldOpen"][0])}</a>' if nh else ""
    o.append(f'<dt data-i18n="fldNext">{esc(U["fldNext"][0])}</dt><dd>{both(md(r["next"][0]), md(r["next"][1]), "span")}{link}</dd>')
    o.append("</dl>")
    if r.get("untested_parts"):
        o.append(both(esc(r["untested_parts"][0]), esc(r["untested_parts"][1]), "p", "fld-run"))
    if r.get("code"):
        src = (REPO / "fields/code" / cat / r["code"]).read_text()
        o.append(f'<details><summary data-i18n="fldCode">{esc(U["fldCode"][0])}</summary>'
                 f'<p><a href="/fields/{cat}/code/{r["code"]}" download data-i18n="fldDownload">{esc(U["fldDownload"][0])}</a> · <code>{esc(r["code"])}</code></p>'
                 f'<pre><code>{esc(src)}</code></pre></details>')
    if tested:
        versions = recipe_versions(src, versions)
        tail = "\n".join(run.get("stdout_tail") or [])
        o.append(f'<details><summary data-i18n="fldBsvRun">{esc(U["fldBsvRun"][0])}</summary>'
                 f'<p class="fld-run"><span data-i18n="fldRunAt">{esc(U["fldRunAt"][0])}</span> {esc(run["date_jst"])} JST · {esc(versions)}</p>'
                 f'<pre><code>{esc(tail)}</code></pre></details>')
    else:
        o.append(f'<p class="fld-run" data-i18n="fldNotRunWhy">{esc(U["fldNotRunWhy"][0])}</p>')
    o.append("</article>")
    return "\n".join(o), tested


def labs(site):
    """Field Labs (Astra/Codex browser tools) shipped by build_field_labs.py in the same build: {field: entry}."""
    p = site / "labs/catalog.json"
    if not p.exists():
        return {}
    return {e["field"]: e for e in json.loads(p.read_text()).get("entries", []) if (site / e["url"].lstrip("/") / "index.html").exists()}


def field_page(site, cat, f, runs, checks, versions, css_href, js_href, lab=None):
    U = C.UI
    recs, tested = [], 0
    for r in f["recipes"]:
        h, ok = recipe_html(cat, r, runs, versions)
        recs.append(h)
        tested += ok
    rows = []
    for tool, url, job, lic, diff, where in f["compare"]:
        if checks.get(url, {}).get("status") != 200:
            raise SystemExit(f"fields: compare URL not verified 200: {url}")
        rows.append(f'<tr><td><a href="{esc(url)}" rel="noopener" target="_blank">{esc(tool)}</a></td><td>{both(esc(job[0]), esc(job[1]), "span")}</td>'
                    f'<td>{esc(lic)}</td><td data-i18n="diff_{diff}">{esc(U["diff_" + diff][0])}</td><td data-i18n="where_{where}">{esc(U["where_" + where][0])}</td></tr>')
    stack, skipped = [], []
    for name, url, org, lic, summ in f["stack"]:
        c = checks.get(url, {})
        if c.get("status") != 200:
            skipped.append(url)
            continue
        stack.append(f'<li><h3><a href="{esc(url)}" rel="noopener" target="_blank">{esc(name)}</a></h3>'
                     f'<p class="fld-meta"><span data-i18n="fldOrg">{esc(U["fldOrg"][0])}</span>: {esc(org)} · <span data-i18n="fldLicense">{esc(U["fldLicense"][0])}</span>: {esc(lic)}</p>'
                     f'{both(esc(summ[0]), esc(summ[1]))}'
                     f'<p class="fld-meta"><span data-i18n="fldChecked">{esc(U["fldChecked"][0])}</span>: {esc(c["checked_jst"])} · HTTP {c["status"]}</p></li>')
    th = "".join(f'<th data-i18n="{k}">{esc(U[k][0])}</th>' for k in ("fldTool", "fldJob", "fldLicense", "fldDifficulty", "fldWhere"))
    rel = "".join(f'<li><a href="{h}">{both(esc(t[0]), esc(t[1]), "span")}</a></li>' for h, t in f["related"])
    rel += f'<li><a href="/fields/" data-i18n="fldAllCats">{esc(U["fldAllCats"][0])}</a></li>'
    notice = f'<p class="fld-notice" data-i18n="fld_{cat}_notice">{esc(f["notice"][0])}</p>' if f.get("notice") else ""
    if lab:
        notice += (f'<p class="fld-lab" id="lab"><span class="fld-meta" data-i18n="fldLab">{esc(U["fldLab"][0])}</span><br>'
                   f'<a href="{esc(lab["url"])}" data-lang-show="en" data-evt="fields_lab_{cat}">{esc(lab["title"]["en"])} →</a>'
                   f'<a href="{esc(lab["url"])}?lang=ja" data-lang-show="ja" hidden data-evt="fields_lab_{cat}">{esc(lab["title"]["ja"])} →</a><br>'
                   f'{both(esc(lab["summary"]["en"]), esc(lab["summary"]["ja"]), "span", "fld-meta")}</p>')
    body = f"""{crumbs_html([("/fields/", "fldAllCats", U["fldAllCats"][0]), (None, f"fld_{cat}_name", f["name"][0])])}
<h1 data-i18n="fld_{cat}_h1">{esc(f["h1"][0])}</h1>
<p class="fld-lead" data-i18n="fld_{cat}_lead">{esc(f["lead"][0])}</p>
{notice}
<ul class="fld-toc" aria-label="On this page">
<li><a href="#recipes" data-i18n="fldRecipes">{esc(U["fldRecipes"][0])}</a> ({len(recs)})</li>
<li><a href="#compare" data-i18n="fldCompare">{esc(U["fldCompare"][0])}</a> ({len(rows)})</li>
<li><a href="#stack" data-i18n="fldStack">{esc(U["fldStack"][0])}</a> ({len(stack)})</li>
</ul>
<section id="recipes">
<h2 data-i18n="fldRecipes">{esc(U["fldRecipes"][0])}</h2>
<p class="fld-sublead" data-i18n="fldRecipesLead">{esc(U["fldRecipesLead"][0])}</p>
{chr(10).join(recs)}
</section>
<section id="compare">
<h2 data-i18n="fldCompare">{esc(U["fldCompare"][0])}</h2>
<p class="fld-sublead" data-i18n="fldCompareLead">{esc(U["fldCompareLead"][0])}</p>
<div class="fld-tablewrap"><table><thead><tr>{th}</tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table></div>
</section>
<section id="stack">
<h2 data-i18n="fldStack">{esc(U["fldStack"][0])}</h2>
<p class="fld-sublead" data-i18n="fldStackLead">{esc(U["fldStackLead"][0])}</p>
<ul class="fld-stack">
{chr(10).join(stack)}
</ul>
</section>
<section>
<h2 data-i18n="fldRelated">{esc(U["fldRelated"][0])}</h2>
<ul class="fld-related">{rel}</ul>
</section>"""
    crumbs = [("/", "BotShelf Vampire"), ("/fields/", U["fldHubTitle"][0]), (f"/fields/{cat}/", f["name"][0])]
    d = site / "fields" / cat
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(doc(site, f"/fields/{cat}/", f"fld_{cat}_title", f["name"][0], f["lead"][0], crumbs, body, css_href, js_href))
    cd = d / "code"
    if cd.exists():
        shutil.rmtree(cd)
    cd.mkdir()
    for r in f["recipes"]:
        if r.get("code"):
            shutil.copyfile(REPO / "fields/code" / cat / r["code"], cd / r["code"])
    return {"url": f"/fields/{cat}/", "recipes": len(recs), "tested": tested, "compare": len(rows), "sources": len(stack), "tools": 1 if lab else 0,
            "tool_url": lab["url"] if lab else None, "skipped_sources": skipped}


def hub_page(site, counts, css_href, js_href):
    U = C.UI
    cards = []
    for cat in ORDER:
        f, c = C.F[cat], counts[cat]
        cards.append(f'<li><a href="/fields/{cat}/" data-evt="fields_hub_{cat}"><strong data-i18n="fld_{cat}_name">{esc(f["name"][0])}</strong>'
                     f'<span data-i18n="fld_{cat}_lead">{esc(f["lead"][0])}</span>'
                     f'<span class="fld-meta">{c["recipes"]} <span data-i18n="fldUnitRecipes">{esc(U["fldUnitRecipes"][0])}</span> ({c["tested"]} <span data-i18n="fldUnitTested">{esc(U["fldUnitTested"][0])}</span>) · '
                     f'{c["sources"]} <span data-i18n="fldUnitSources">{esc(U["fldUnitSources"][0])}</span>'
                     + (f' · {c["tools"]} <span data-i18n="fldUnitTools">{esc(U["fldUnitTools"][0])}</span>' if c["tools"] else "") + '</span></a></li>')
    body = f"""{crumbs_html([(None, "fldHubTitle", U["fldHubTitle"][0])])}
<h1 data-i18n="fldHubTitle">{esc(U["fldHubTitle"][0])}</h1>
<p class="fld-lead" data-i18n="fldHubLead">{esc(U["fldHubLead"][0])}</p>
<ul class="fld-cats">
{chr(10).join(cards)}
</ul>"""
    crumbs = [("/", "BotShelf Vampire"), ("/fields/", U["fldHubTitle"][0])]
    (site / "fields/index.html").write_text(doc(site, "/fields/", "fld_hub_title", U["fldHubTitle"][0], U["fldHubLead"][0], crumbs, body, css_href, js_href))


SEARCH_JS_PATCH = (  # (old, new) on the /search/ page script: adds the "fields" scope (Fields & labs)
    ("build: ['ビルドライブラリ', 'Build Library'] };", "build: ['ビルドライブラリ', 'Build Library'], fields: ['分野・ラボ', 'Fields & labs'] };"),
    ("counts = { trading: 0, ai: 0, build: 0 };", "counts = { trading: 0, ai: 0, build: 0, fields: 0 };"),
    ("s === 'all' ? counts.trading + counts.ai + counts.build :", "s === 'all' ? counts.trading + counts.ai + counts.build + counts.fields :"),
    ("sc === 'build' || sc === 'aiall'", "sc === 'build' || sc === 'fields' || sc === 'aiall'"),
)
SEARCH_VER = "v20261007"


def search(site, counts, lb):
    """Add the field pages, recipes and Field Labs to /search/ as scope "fields". The index and page script referenced by
    /search/index.html (written by build_live_toolkit.py, which drops fields/ and labs/ rows) are copied to new
    {SEARCH_VER} names, so cached copies of the old script never meet rows they cannot render."""
    sp = site / "search/index.html"
    sh = sp.read_text()
    js_name = re.search(r"/js/(bsv-search-page\.v[0-9a-z]+\.js)", sh).group(1)
    pj = (site / "js" / js_name).read_text()
    idx_name = re.search(r"(index\.v[0-9a-z]+\.json)", pj).group(1)
    idx = json.loads((site / "search" / idx_name).read_text())
    rows = [r for r in idx["rows"] if not str(r.get("id", "")).startswith(("fields/", "labs/"))]
    U = C.UI
    add = [{"s": "fields", "id": "fields/", "t": U["fldHubTitle"][0], "tj": U["fldHubTitle"][1], "k": "Field hub", "kj": "分野一覧", "c": "Fields", "p": [],
            "d": U["fldHubLead"][0], "dj": U["fldHubLead"][1], "x": "healthcare medical robotics space biotech quantum ヘルスケア 医療 宇宙 バイオ 量子", "u": "/fields/", "a": "free"}]
    for cat in ORDER:
        f = C.F[cat]
        tools = [c[0] for c in f["compare"]]
        add.append({"s": "fields", "id": f"fields/{cat}", "t": f["name"][0], "tj": f["name"][1], "k": "Field", "kj": "分野", "c": f["name"][0], "p": tools[:3],
                    "d": f["lead"][0], "dj": f["lead"][1], "x": " ".join(tools + [s[0] for s in f["stack"]] + [r["title"][0] + " " + r["title"][1] for r in f["recipes"]]),
                    "u": f"/fields/{cat}/", "a": "free"})
        for r in f["recipes"]:
            add.append({"s": "fields", "id": f"fields/{cat}/{r['id']}", "t": r["title"][0], "tj": r["title"][1], "k": "Recipe", "kj": "作り方レシピ", "c": f["name"][0],
                        "p": [], "d": r["summary"][0], "dj": r["summary"][1], "x": f'{f["name"][1]} {r["prereq"][0]} {r["code"] or ""}',
                        "u": f"/fields/{cat}/#{r['id']}", "a": "free"})
        if cat in lb:
            e = lb[cat]
            add.append({"s": "fields", "id": f"labs/{cat}", "t": e["title"]["en"], "tj": e["title"]["ja"], "k": "Interactive tool", "kj": "インタラクティブツール",
                        "c": f["name"][0], "p": [], "d": e["summary"]["en"], "dj": e["summary"]["ja"], "x": f'Field Labs 実践ラボ browser {f["name"][1]}',
                        "u": e["url"], "uj": e["url"] + "?lang=ja", "a": "free"})
    if lb:
        add.append({"s": "fields", "id": "labs/", "t": "BSV Field Labs", "tj": "BSV 実践ラボ", "k": "Interactive tools", "kj": "インタラクティブツール", "c": "Fields", "p": [],
                    "d": "Four browser tools for medical robotics, space, biotech and quantum (English / Japanese).",
                    "dj": "医療ロボティクス・宇宙・バイオ・量子の4つのブラウザツール（英語／日本語）。", "x": "labs tools", "u": "/labs/", "uj": "/labs/?lang=ja", "a": "free"})
    clean = dict(idx, rows=rows)
    clean["counts"] = {k: v for k, v in idx.get("counts", {}).items() if k != "fields"}
    (site / "search" / idx_name).write_text(json.dumps(clean, ensure_ascii=False, separators=(",", ":")))
    out = dict(clean, rows=rows + add)
    out["counts"] = dict(clean["counts"], fields=len(add))
    new_idx, new_js = f"index.{SEARCH_VER}.json", f"bsv-search-page.{SEARCH_VER}.js"
    (site / "search" / new_idx).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    js = pj.replace(idx_name, new_idx)
    for a, b in SEARCH_JS_PATCH:
        if b not in js:
            if a not in js:
                raise SystemExit(f"search page script changed; cannot patch: {a}")
            js = js.replace(a, b)
    (site / "js" / new_js).write_text(js)
    if js_name != new_js:
        # build_live_toolkit copies the currently referenced (already patched) script to its own older name; restore
        # that published, immutable file to its unpatched form so a rebuild never changes its bytes.
        base_js = pj
        for a, b in SEARCH_JS_PATCH:
            base_js = base_js.replace(b, a)
        (site / "js" / js_name).write_text(base_js)
    btn = '<button type="button" role="tab" data-scope="fields" data-en="Fields &amp; labs" data-ja="分野・ラボ">Fields &amp; labs</button>'
    if 'data-scope="fields"' not in sh:
        anchor = re.search(r'<button type="button" role="tab" data-scope="build"[^>]*>[^<]*</button>', sh).group(0)
        sh = sh.replace(anchor, anchor + "\n  " + btn)
    sp.write_text(sh.replace(f"/js/{js_name}", f"/js/{new_js}"))
    return {"search_rows_added": len(add), "index": new_idx, "script": new_js}


def favicon(site):
    """/favicon.ico from the existing mark (img/mark.jpg): browsers request it on pages without a <link rel=icon>."""
    from PIL import Image
    p = site / "favicon.ico"
    if not p.exists():
        Image.open(site / "img/mark.jpg").convert("RGBA").save(p, sizes=[(16, 16), (32, 32), (48, 48)])
    return p.exists()


def sitemap(site, urls):
    smp = site / "sitemap.xml"
    sm = smp.read_text()
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d")
    add = "".join(f"  <url><loc>{ORIGIN}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls if f"<loc>{ORIGIN}{u}</loc>" not in sm)
    if add:
        smp.write_text(sm.replace("</urlset>", add + "</urlset>"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    site = Path(ap.parse_args().site)
    tr = json.loads((REPO / "fields/test_runs.json").read_text())
    checks = json.loads((REPO / "fields/sources_check.json").read_text())
    css_href, js_href = assets(site)
    counts, lb = {}, labs(site)
    for cat in ORDER:
        f = C.F[cat]
        counts[cat] = field_page(site, cat, f, tr["runs"], checks, tr, css_href, js_href, lb.get(cat))
    hub_page(site, counts, css_href, js_href)
    out = {"generated_jst": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"),
           "method": "Counts are computed by build_fields.py from fields_content.py, fields/test_runs.json, fields/sources_check.json and /labs/catalog.json (one interactive tool per field when shipped). 'tested' = BSV ran the recipe's own script and it produced its expected files.",
           "categories": counts}
    (site / "fields/index.json").write_text(json.dumps(out, indent=1) + "\n")
    sres = search(site, counts, lb)
    favicon(site)
    sitemap(site, ["/fields/"] + [f"/fields/{c}/" for c in ORDER] + (["/labs/"] + [lb[c]["url"] for c in ORDER if c in lb] if lb else []))
    print(json.dumps({"fields": {c: {k: counts[c][k] for k in ("recipes", "tested", "compare", "sources")} for c in ORDER},
                      "skipped_sources": sum(len(c["skipped_sources"]) for c in counts.values()), **sres}))


if __name__ == "__main__":
    main()
