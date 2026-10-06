#!/usr/bin/env python3
"""Regression test for the BSV field pages built by build_fields.py.
usage: test_fields.py --site <site>"""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fields_content as C

REPO = Path(__file__).resolve().parents[2]
CLAIMS = re.compile(r"\b(cures?|treat(s|ment|ing)?|diagnos\w*|therap\w*|guarantee\w*)\b|治療|診断|保証", re.I)
REWARD = re.compile(r"referral|affiliate|IB reward|rebate|紹介報酬|キャッシュバック|アフィリエイト", re.I)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True)
    s = Path(ap.parse_args().site)
    n, fails = [0], []
    def ok(c, m):
        n[0] += 1
        if not c: fails.append(m)
    idx = json.loads((s / "fields/index.json").read_text())["categories"]
    runs = json.loads((REPO / "fields/test_runs.json").read_text())["runs"]
    checks = json.loads((REPO / "fields/sources_check.json").read_text())
    js = sorted((s / "fields").glob("fields-i18n.*.js"))
    ok(len(js) == 1, "one fields-i18n bundle")
    pj = json.loads(re.search(r"window\.PAGE_I18N=(\{.*\});", js[0].read_text(), re.S).group(1)) if js else {}
    ok((s / "fields/index.html").exists(), "/fields/ hub exists")
    for cat, f in C.F.items():
        p = s / "fields" / cat / "index.html"
        ok(p.exists(), f"{cat}: page exists")
        if not p.exists(): continue
        t = p.read_text()
        arts = re.findall(r'<article class="fld-recipe" id="([a-z0-9-]+)">(.*?)</article>', t, re.S)
        ok(3 <= len(arts) <= 12 and len(arts) == idx[cat]["recipes"], f"{cat}: 3-12 recipes, matches index.json ({len(arts)})")
        for rid, body in arts:
            for k in ("fldInput", "fldOutput", "fldPrereq", "fldSteps", "fldExpected", "fldNext"):
                ok(f'data-i18n="{k}"' in body, f"{cat}/{rid}: has {k}")
            r = next(x for x in f["recipes"] if x["id"] == rid)
            run = runs.get(r.get("code") or "")
            tested = bool(run and run["ok"] and run["files_ok"])
            ok(("fld-badge-ok" in body) == tested and ("fld-badge-no" in body) == (not tested), f"{cat}/{rid}: badge matches test_runs.json")
            ok(("fldBsvRun" in body) == tested, f"{cat}/{rid}: real output only when tested")
        ok(sum(1 for _, b in arts if "fld-badge-ok" in b) == idx[cat]["tested"], f"{cat}: tested count matches")
        rows = re.findall(r"<tr><td><a href=\"([^\"]+)\"", t)
        ok(len(rows) == idx[cat]["compare"] and len(rows) >= 3, f"{cat}: comparison rows")
        ok(all(k in t for k in ('data-i18n="fldTool"', 'data-i18n="fldJob"', 'data-i18n="fldLicense"', 'data-i18n="fldDifficulty"', 'data-i18n="fldWhere"')), f"{cat}: table columns")
        stack = re.findall(r'<ul class="fld-stack">(.*?)</ul>', t, re.S)[0]
        srcs = re.findall(r'<h3><a href="([^"]+)"', stack)
        ok(len(srcs) == idx[cat]["sources"] and srcs, f"{cat}: stack count matches")
        ok(all(checks.get(u, {}).get("status") == 200 for u in srcs + rows), f"{cat}: every outbound source checked HTTP 200")
        ok(stack.count("HTTP 200") == len(srcs), f"{cat}: each source shows its check")
        code = {x.name for x in (s / "fields" / cat / "code").glob("*")}
        ok(code == {r["code"] for r in f["recipes"] if r.get("code")}, f"{cat}: only BSV's own recipe code shipped")
        ok(all((s / "fields" / cat / "code" / c).read_bytes() == (REPO / "fields/code" / cat / c).read_bytes() for c in code), f"{cat}: code = repo source")
        vis = re.sub(r"<[^>]+>", " ", re.sub(r"<pre>.*?</pre>", " ", t, flags=re.S))
        ok(not CLAIMS.search(vis), f"{cat}: no clinical / guarantee claims ({CLAIMS.search(vis)})")
        ok(not REWARD.search(vis), f"{cat}: no reward wording")
        ok('rel="canonical" href="https://botshelfvampire.com/fields/' + cat + '/"' in t and "BreadcrumbList" in t, f"{cat}: canonical + breadcrumbs")
        ok("style=" not in t.split("<main", 1)[1], f"{cat}: no inline style")
        lab = idx[cat].get("tool_url")
        ok(idx[cat]["tools"] == (1 if lab else 0) and (not lab or (f'href="{lab}"' in t and (s / lab.lstrip("/") / "index.html").exists())), f"{cat}: Field Lab link matches index.json")
        if cat == "healthcare":
            ok('data-i18n="fld_healthcare_notice"' in t and "Research, education and simulation only" in t, "healthcare: research/education/simulation notice")
        for key in set(re.findall(r'data-i18n="([A-Za-z0-9_-]+)"', t)) - {"navRegister"}:
            ok(all(pj.get(l, {}).get(key) for l in C.LANGS), f"{cat}: i18n key {key} in 5 languages")
        ok(t.count('data-lang-show="en"') == t.count('data-lang-show="ja"'), f"{cat}: en/ja bodies paired")
    sh = (s / "search/index.html").read_text()
    jsn = re.search(r"/js/(bsv-search-page\.v[0-9a-z]+\.js)", sh).group(1)
    pjs = (s / "js" / jsn).read_text()
    si = json.loads((s / "search" / re.search(r"(index\.v[0-9a-z]+\.json)", pjs).group(1)).read_text())
    fr = [r for r in si["rows"] if r.get("s") == "fields"]
    want = 1 + sum(idx[c]["recipes"] + 1 + idx[c]["tools"] for c in idx) + (1 if any(idx[c]["tools"] for c in idx) else 0)
    ok(len(fr) == want == si["counts"].get("fields"), f"search: {len(fr)} fields rows (want {want})")
    ok(all((s / r["u"].split("#")[0].lstrip("/") / "index.html").exists() for r in fr), "search: every fields row points to a shipped page")
    ok('data-scope="fields"' in sh and "fields: ['分野・ラボ', 'Fields & labs']" in pjs and "counts.fields" in pjs, "search: Fields & labs scope wired")
    old = [p for p in (s / "search").glob("index.v*.json") if p.name not in pjs]
    ok(not any(r.get("s") == "fields" for p in old for r in json.loads(p.read_text())["rows"]), "search: older indexes carry no fields rows (cached old scripts stay safe)")
    oldjs = [p for p in (s / "js").glob("bsv-search-page.v*.js") if p.name != jsn]
    ok(not any("fields: ['分野・ラボ'" in p.read_text() for p in oldjs), "search: older page scripts keep their published (no fields scope) bytes")
    ok((s / "favicon.ico").exists(), "favicon.ico shipped")
    sm = (s / "sitemap.xml").read_text()
    ok(all(f"<loc>https://botshelfvampire.com/fields/{c}</loc>" in sm for c in [x + "/" for x in C.F] + [""]) , "sitemap has /fields/ pages")
    print(json.dumps({"test": "fields", "checks": n[0], "failures": len(fails), "fail": fails[:10]}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
