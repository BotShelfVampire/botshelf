#!/usr/bin/env python3
"""Checks for Issue #8 tranche 1 (robots, sitemap, canonical, llms.txt, trust manifest, JSON-LD).

--site checks the built site; --live additionally fetches production and re-reads every trust fact
from the live page (fresh read), checks llms.txt URLs return 200 and gated source stays gated.
"""
import argparse, json, re, sys, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import build_discovery as bd

ORIGIN = bd.ORIGIN
fails, n = [], 0


def ok(c, msg):
    global n
    n += 1
    if not c:
        fails.append(msg)


class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def get(u, ua="Mozilla/5.0 BSV-discovery-check"):
    op = urllib.request.build_opener(NoRedir)
    try:
        r = op.open(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=30)
        return r.status, r.read().decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers or {})


def groups(robots_txt):
    g, cur = {}, None
    for l in robots_txt.splitlines():
        l = l.split("#", 1)[0].strip()
        if not l:
            continue
        k, _, v = l.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            cur = v
            g.setdefault(cur, [])
        elif cur:
            g[cur].append((k, v))
    return g


def check_text(site_files):
    rb, sm, ll, tj, idx = site_files
    g = groups(rb)
    ok("OAI-SearchBot" in g and ("allow", "/") in g["OAI-SearchBot"], "robots: OAI-SearchBot allow /")
    ok(g.get("GPTBot") == [("disallow", "/")], "robots: GPTBot disallow /")
    star_dis = [x for x in g.get("*", []) if x[0] == "disallow"]
    ok(star_dis and all(x in g.get("OAI-SearchBot", []) for x in star_dis), "robots: OAI-SearchBot keeps * Disallow list")
    ok(("allow", "/") in g.get("*", []), "robots: * allow / unchanged")
    ok("Sitemap: https://botshelfvampire.com/sitemap.xml" in rb, "robots: sitemap line")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    ok(len(locs) == len(set(locs)), "sitemap: no duplicate URLs")
    ok(ORIGIN + "/index.html" not in locs and ORIGIN + "/packs.html" not in locs, "sitemap: no /index.html or /packs.html")
    m = json.loads(tj)
    ok(m["sellerEconomics"]["sellerSharePercent"] == 80 and m["sellerEconomics"]["bsvSharePercent"] == 20, "trust: 80/20")
    ok(m["payments"]["network"] == "TRC20" and m["payments"]["card"] is False, "trust: TRC20, no card")
    ok(m["listingRules"]["paidMonthlyMinimumUSDT"] == 15 and m["listingRules"]["ibLinkMonthlyFeeUSDT"] == 250, "trust: 15 / 250")
    ok(m["tradersLibrary"]["runtimeTestedByBSV"] == 0, "trust: runtime-tested 0")
    ok("operatorDisclosure" not in m, "trust: no operator-positioning text (proposal only)")
    ok(m["supportEmail"] == "support@botshelfvampire.com", "trust: support email")
    ok(ll.count(bd.LL_BEGIN) == 1 and "/.well-known/bsv-trust.json" in ll, "llms: one discovery block with trust link")
    ok(not re.search(r"/(trading|library)/(sources|items|downloads|source)/[a-z0-9]", ll), "llms: no gated source URLs")
    ok('"email":"support@botshelfvampire.com"' in idx, "jsonld: Organization email")
    return locs, m


def schema_errors(x, sc, path="$"):
    """Small JSON Schema subset (type, const, enum, required, additionalProperties:false, properties, items,
    minItems, minLength, maxLength, minimum, pattern) — enough for the BSV v0.1 schemas."""
    errs = []
    T = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
    def is_t(v, t):
        if t == "integer":
            return isinstance(v, int) and not isinstance(v, bool)
        if t == "number":
            return isinstance(v, (int, float)) and not isinstance(v, bool)
        return isinstance(v, T[t])
    ts = sc.get("type")
    if ts and not any(is_t(x, t) for t in ([ts] if isinstance(ts, str) else ts)):
        return [f"{path}: type {type(x).__name__} not {ts}"]
    if "const" in sc and x != sc["const"]:
        errs.append(f"{path}: const")
    if "enum" in sc and x not in sc["enum"]:
        errs.append(f"{path}: enum {x!r}")
    if isinstance(x, str):
        if len(x) < sc.get("minLength", 0) or len(x) > sc.get("maxLength", 10**9):
            errs.append(f"{path}: length")
        if "pattern" in sc and not re.search(sc["pattern"], x):
            errs.append(f"{path}: pattern")
    if isinstance(x, (int, float)) and not isinstance(x, bool) and "minimum" in sc and x < sc["minimum"]:
        errs.append(f"{path}: minimum")
    if isinstance(x, dict):
        for k in sc.get("required", []):
            if k not in x:
                errs.append(f"{path}: missing {k}")
        props = sc.get("properties", {})
        if sc.get("additionalProperties") is False:
            errs += [f"{path}: extra {k}" for k in x if k not in props]
        for k, v in x.items():
            if k in props:
                errs += schema_errors(v, props[k], f"{path}.{k}")
    if isinstance(x, list):
        if len(x) < sc.get("minItems", 0):
            errs.append(f"{path}: minItems")
        if isinstance(sc.get("items"), dict):
            for n, v in enumerate(x):
                errs += schema_errors(v, sc["items"], f"{path}[{n}]")
    return errs


class _NoRedirect(__import__("urllib.request").request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def status_no_redirect(u, tries=3):
    import time, urllib.request, urllib.error
    op = urllib.request.build_opener(_NoRedirect)
    for k in range(tries):  # -1 = network error (no HTTP status); retried, an HTTP status is never retried
        try:
            r = op.open(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0 BSV-discovery-check"}), timeout=30)
            return r.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            time.sleep(1 + k)
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--live", default="")
    a = ap.parse_args()
    s = Path(a.site)
    rd = lambda p: (s / p).read_text(errors="ignore")
    locs, m = check_text((rd("robots.txt"), rd("sitemap.xml"), rd("llms.txt"), rd(".well-known/bsv-trust.json"), rd("index.html")))
    # every sitemap HTML page: indexable, canonical == URL; all JSON-LD parses
    for u in locs:
        f = bd.url_to_file(s, u)
        ok(f.exists(), f"sitemap: file for {u}")
        if f.suffix == ".html" and f.exists():
            rb, cn = bd.head_meta(f.read_text(errors="ignore"))
            ok("noindex" not in rb, f"sitemap: noindex page {u}")
            ok(cn == u, f"canonical: {u} -> {cn}")
    bad = 0
    for f in s.rglob("*.html"):
        for mm in re.finditer(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", f.read_text(errors="ignore"), re.S):
            try:
                json.loads(mm.group(1))
            except Exception:
                bad += 1
    ok(bad == 0, f"jsonld: {bad} invalid blocks")
    # Request Market page (Issue #6): no seeded rows/numbers in HTML, no inline JS, schema published
    rq = s / "requests/index.html"
    if rq.exists():
        t = rq.read_text()
        ok(ORIGIN + "/requests/" in locs, "requests: in sitemap")
        ok(not re.search(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", t), "requests: no inline script")
        ok("req_" not in t and all(re.search(rf'id="{i}">–<', t) for i in ("rq-c-received", "rq-c-published", "rq-c-budget")), "requests: no seeded requests or counts in HTML")
        ok('id="rq-form"' in t and "/register.html?next=/requests/" in "".join(p.read_text() for p in (s / "requests").glob("request-market.*.js")), "requests: form + sign-in path")
        op = json.loads((s / "requests/opportunities.json").read_text())
        cat = json.loads((s / "trading/catalog.json").read_text())
        g = {x["id"]: x for x in op["signals"]["catalogueGaps"]["gaps"]}
        ok(g["tradingview-only"]["count"] == sum(1 for i in cat if set(i["platforms"]) == {"TradingView"}), "opportunities: TradingView-only count matches catalog")
        ok(g["mt-no-pine"]["count"] == sum(1 for i in cat if "TradingView" not in i["platforms"]), "opportunities: MT-only count matches catalog")
        ok(all(x["count"] == len(x["entries"]) for x in g.values()), "opportunities: counts equal listed entries")
        osch = json.loads((s / "schemas/opportunity-signal-v0.1.json").read_text())
        ok((s / "schemas/opportunity-signal-v0.1.json").read_text() == (bd.Path(__file__).resolve().parents[2] / "schemas/bsv-opportunity-signal.schema.json").read_text() and op["signals"]["opportunitySignals"]["schema"].endswith("/schemas/opportunity-signal-v0.1.json"), "opportunity-signal schema published byte-identical and linked")
        # generator gaps (#6 tranche 6): every listed recipe really uses the block type; counts add up; page table = json
        gg = op["signals"]["generatorGaps"]; rdir = bd.Path(__file__).resolve().parents[2] / "trader-toolkit/recipes"
        uses = lambda stem, ty: any(b.get("type") == ty for b in json.loads((rdir / f"{stem}.json").read_text())["blocks"])
        ok(gg["targets"] == 22 and gg["gaps"] and all(g["recipeCount"] == len(g["recipes"]) and g["targetsWithIt"] + g["targetsWithoutIt"] == gg["targets"] and all(uses(r, g["blockType"]) for r in g["recipes"]) for g in gg["gaps"]), "opportunities: generator gaps are real block types in the listed recipes")
        ok(gg["recipesWithGaps"] == len({r for g in gg["gaps"] for r in g["recipes"]}), "opportunities: recipesWithGaps equals listed recipes")
        prow = re.findall(r'<tr id="gap-([a-z_.]+)"><td><code>[^<]*</code></td><td>(\d+) ', t)
        ok(prow == [(g["blockType"], str(g["recipeCount"])) for g in gg["gaps"]], f"requests page: generator-gap table equals opportunities.json ({len(prow)} rows)")
        ok(re.findall(r'data-ask="([a-z_.]+)" href="/requests/\?area=trading&amp;block=\1#rq-form"', t) == [g["blockType"] for g in gg["gaps"]], "requests page: one ask-for-it link per generator gap (#6 tranche 9)")
        rmj = [p for p in (s / "requests").glob("request-market.*.js")]
        ok(len(rmj) == 1 and "q.get('block')" in rmj[0].read_text() and "!jb.value" in rmj[0].read_text() and 'value="trading"' in t, "requests page: block prefill fills the job box only when empty; trading area exists")
        ok(op["signals"]["noResultSearches"]["collected"] is False and op["signals"]["pageViews"]["collected"] is False, "opportunities: uncollected signals marked, not invented")
        # generator coverage (#8 tranche 7): every target listed once, check scripts exist, TODO totals agree with gaps
        cv = json.loads((s / "trading/build/coverage.json").read_text()); repo = bd.Path(__file__).resolve().parents[2]
        ok(len(cv["targets"]) == 22 and len({x["id"] for x in cv["targets"]}) == 22 and all((repo / x["check"]["script"]).exists() and x["runtimeTestedByBSV"] is False for x in cv["targets"]) and cv["counts"]["runtimeTestedByBSV"] == 0, "coverage.json: 22 targets, check scripts exist, runtimeTestedByBSV 0")
        ok(sum(cv["counts"]["byCheckKind"].values()) == 22 and cv["counts"]["byCheckKind"].get("PARITY_ONLY") == 22 - sum(1 for x in cv["targets"] if x["check"]["kind"] != "PARITY_ONLY"), "coverage.json: check-kind counts add up")
        ok(len(cv["recipes"]) == gg["recipes"] and all(set(r["todoLines"]) == {x["id"] for x in cv["targets"]} for r in cv["recipes"]) and {b for r in cv["recipes"] for b in r["unsupportedBlocks"]} == {g["blockType"] for g in gg["gaps"]}, "coverage.json: recipes x targets complete; unsupported blocks equal generator gaps")
        hs = {x["id"]: x["higherTimeframe"]["status"] for x in cv["targets"]}
        ok({k for k, v in hs.items() if v == "CLOSED_BARS_CHECKED"} == {"backtrader", "backtesting-py", "nautilus"} and {k for k, v in hs.items() if v == "CLOSED_BAR_IDIOM_STATIC"} == {"pine-v6", "mql5", "mql4", "ninjatrader"} and all(v in ("CLOSED_BARS_CHECKED", "CLOSED_BAR_IDIOM_STATIC", "UNSUPPORTED_TODO") for v in hs.values()) and cv["counts"]["higherTimeframeReal"] == 3 and cv["counts"]["higherTimeframeDocumentedIdiom"] == 4 and "chart timeframe" in cv["higherTimeframeDisclosure"], "coverage.json: higher-timeframe status per target + correction disclosed")
        ok(all(x["higherTimeframe"].get("docs") and all(u.startswith(("https://www.tradingview.com/pine-script-docs/", "https://www.mql5.com/en/docs/", "https://docs.mql4.com/", "https://ninjatrader.com/support/helpGuides/nt8/")) for u in x["higherTimeframe"]["docs"]) and "UNTESTED_RUNTIME" in x["higherTimeframe"]["note"] and x["runtimeTestedByBSV"] is False for x in cv["targets"] if hs[x["id"]] == "CLOSED_BAR_IDIOM_STATIC"), "coverage.json: documented-idiom targets cite official docs and stay UNTESTED_RUNTIME")
        mp = s / "trading/tools/bsv-recipe-mtf-confirmation-panel.html"
        ok(mp.exists() and ('id="higher-timeframe"' in mp.read_text() and "Correction (2026-10-04)" in mp.read_text()), "recipe page: higher-timeframe notice on mtf-confirmation-panel")
        cp = s / "trading/build/coverage/index.html"; ct = cp.read_text() if cp.exists() else ""
        ok(ORIGIN + "/trading/build/coverage/" in locs and re.findall(r'<tr id="cov-([a-z0-9-]+)"><td>', ct) == [x["id"] for x in cv["targets"]], "coverage page: in sitemap, one row per target in coverage.json order")
        ok(re.findall(r'data-kind="([A-Z_]+)"', ct) == [x["check"]["kind"] for x in cv["targets"]] and re.findall(r'data-htf="([A-Z_]+)"', ct) == [x["higherTimeframe"]["status"] for x in cv["targets"]], "coverage page: check kind and higher-timeframe status equal coverage.json")
        ok([int(n) for n in re.findall(r'<td data-n="(\d+)">', ct)] == [r["todoLines"][x["id"]] for r in cv["recipes"] for x in cv["targets"]], "coverage page: TODO matrix equals coverage.json")
        import csv as _csv  # coverage.csv (#8 tranche 9): same matrix and statuses as coverage.json
        cr = list(_csv.reader((s / "trading/build/coverage.csv").read_text().splitlines())) if (s / "trading/build/coverage.csv").exists() else [[]]
        cut = cr.index([]) if [] in cr else len(cr)
        ok(cr[0] == ["recipe"] + [x["id"] for x in cv["targets"]] and [[r[0]] + [int(v) for v in r[1:]] for r in cr[1:cut]] == [[r["id"]] + [r["todoLines"][x["id"]] for x in cv["targets"]] for r in cv["recipes"]]
           and [r[3] for r in cr[cut + 2:]] == [x["higherTimeframe"]["status"] for x in cv["targets"]] and all(r[4] == "false" for r in cr[cut + 2:]) and 'href="/trading/build/coverage.csv"' in ct, "coverage.csv equals coverage.json (matrix + statuses) and is linked")
        ok(re.findall(r'data-doc href="([^"]+)"', ct) == [u for x in cv["targets"] for u in x["higherTimeframe"].get("docs", [])], "coverage page: official doc links for documented-idiom targets")
        ok('"@type":"Dataset"' in ct and "/trading/build/coverage.json" in ct and "<script>" not in ct.replace('<script type="application/ld+json">', ""), "coverage page: Dataset JSON-LD for the downloadable file, no inline script")
        tids = [x["id"] for x in cv["targets"]]
        ok(all(g["targetsWithIt"] == len(g["targetsRenderingIt"]) and set(g["targetsRenderingIt"]) <= set(tids) for g in gg["gaps"]), "opportunities: targets rendering each gap listed by id, count matches")
        ok(cv["counts"]["recipeTargetPairsWithoutTodo"] == sum(1 for r in cv["recipes"] for v in r["todoLines"].values() if v == 0), "coverage.json: pairs-without-TODO count matches rows")
        ok(f"{ORIGIN}/trading/build/coverage.json" in (s / "llms.txt").read_text() and json.loads((s / ".well-known/bsv-trust.json").read_text())["generatorCoverage"]["url"].endswith("/trading/build/coverage.json"), "coverage.json: linked from llms.txt and trust manifest")
        ok('id="heatmap"' in t and 'id="rq-heat"' in t and not re.search(r'id="rq-heat"[^>]*>[^<]', t), "requests: demand heatmap present, no seeded cells")
        ok('id="builders"' in t and 'id="rq-areas"' in t and not re.search(r"projected|forecast|potential revenue|\$\d", bd.visible_text(rq), re.I), "opportunities: section present, no revenue projections")
        sc = json.loads((s / "schemas/demand-request-v0.1.json").read_text())
        ok(sc.get("$id") == ORIGIN + "/schemas/demand-request-v0.1.json", "requests: schema published at its $id")
        ok("data-rq-link" in (s / "trading/build/index.html").read_text(), "requests: link from /trading/build/")
    # Transparency Center (Issue #8 tranche 2)
    tp = s / "transparency/index.html"
    if tp.exists():
        t = tp.read_text()
        vt = bd.visible_text(tp)
        ok(ORIGIN + "/transparency/" in locs, "transparency: in sitemap")
        for key, page, sent in bd.FACTS:
            ok(sent in vt, f"transparency quotes {key}")
        cat = json.loads((s / "trading/catalog.json").read_text())
        ok(f"Traders Library entries Traders Library の件数 {len(cat)}" in vt, "transparency: catalogue total matches catalog.json")
        ok(f"runtime-tested by BSV {sum(1 for i in cat if i.get('runtime_tested') is True)}" in vt, "transparency: runtime-tested matches catalog.json")
        ok(all(re.search(rf'id="{i}">–<', t) for i in ("tc-rq-received", "tc-rq-published", "tc-rp-received", "tc-rp-reviewed")), "transparency: live counts not hard-coded")
        ok(all(f'id="{i}"' in t for i in ("money", "buyers", "payouts", "labels", "coverage", "limits", "changes", "incidents", "support", "privacy")), "transparency: 10 sections")
        ok("Sales and payout totals are not published" in vt and "No incident records are published yet" in vt, "transparency: no invented sales or incident figures")
        ok(not re.search(r"low-profile|persona", vt, re.I), "transparency: no operator-positioning text (proposal only)")
        ok(not re.search(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", t), "transparency: no inline script")
        ok(m.get("transparencyCenter") == ORIGIN + "/transparency/", "trust manifest links the Transparency Center")
    nob = [u for u in locs if u != ORIGIN + "/" and bd.url_to_file(s, u).suffix == ".html" and bd.url_to_file(s, u).exists() and "BreadcrumbList" not in bd.url_to_file(s, u).read_text(errors="ignore")]
    ok(not nob, f"breadcrumbs: sitemap pages without BreadcrumbList {nob[:5]}")
    # capability manifests (#8 tranche 3)
    cm = json.loads(rd("capabilities/index.json"))
    csch = json.loads(rd("schemas/capability-manifest-v0.1.json"))
    ok(rd("schemas/capability-manifest-v0.1.json") == (bd.Path(__file__).resolve().parents[2] / "schemas/bsv-capability-manifest.schema.json").read_text(), "capability schema published byte-identical")
    errs = [e for c in cm["capabilities"] for e in schema_errors(c, csch, c.get("capabilityId", "?"))]
    ok(not errs, f"capability manifests validate: {errs[:5]}")
    ok(schema_errors({"schemaVersion": "0.1"}, csch) != [] and schema_errors({**cm["capabilities"][0], "x": 1}, csch) != [], "capability validator rejects bad manifests")
    catj = json.loads(rd("trading/catalog.json"))
    ok(cm["counts"]["catalogue"] == len(catj) == sum(1 for c in cm["capabilities"] if c["capabilityId"].startswith("trading.")), "capabilities: one per catalogue entry")
    ok(cm["counts"]["total"] == len(cm["capabilities"]) and len({c["capabilityId"] for c in cm["capabilities"]}) == len(cm["capabilities"]), "capabilities: counts and unique ids")
    ok(not any(c["verification"]["status"] == "VERIFIED" for c in cm["capabilities"]), "capabilities: nothing VERIFIED")
    ok(sum(1 for c in cm["capabilities"] if c["verification"]["status"] == "PARTIAL") == sum(1 for i in catj if i.get("runtime_tested") is True), "capabilities: PARTIAL only where the catalogue says runtime-tested")
    byid = {c["capabilityId"]: c for c in cm["capabilities"]}
    ok(all(bool(byid["trading." + i["id"]]["sideEffects"]) == (i["kind"] in ("Expert Advisor", "Trade manager", "Strategy")) for i in catj), "capabilities: order side effects declared for EAs, trade managers and strategies")
    cbad = [c["canonicalUrl"] for c in cm["capabilities"] if not (bd.url_to_file(s, c["canonicalUrl"]).exists() and "noindex" not in bd.head_meta(bd.url_to_file(s, c["canonicalUrl"]).read_text(errors="ignore"))[0])]
    ok(not cbad, f"capabilities: canonical URLs are existing indexable pages {cbad[:3]}")
    ok(not re.search(r"local_source|sources/|@[a-z0-9-]+\.[a-z]", json.dumps(cm)) , "capabilities: no gated paths or emails")
    ok(m.get("capabilityManifests", {}).get("url") == ORIGIN + "/capabilities/index.json", "trust manifest links capability manifests")
    ok(ORIGIN + "/capabilities/index.json" in rd("llms.txt"), "llms links capability manifests")
    # readable /capabilities/ page (#8 tranche 5): one row per manifest, status as labelled, public links only
    ch = rd("capabilities/index.html")
    rows = re.findall(r'<tr id="([^"]+)"><td>(?:<a href="([^"]+)">)?.*?<td><code>([A-Z_]+)</code></td>', ch)
    want = {x["capabilityId"]: x["verification"]["status"] for x in cm["capabilities"]}
    ok(len(rows) == len(want) and all(want.get(i) == st for i, _, st in rows), f"capabilities page: {len(rows)} rows = manifests, statuses as labelled")
    ok(not any(h and bd.is_gated(h) for _, h, _ in rows), "capabilities page: no links to gated pages")
    ok(f"<loc>{ORIGIN}/capabilities/</loc>" in rd("sitemap.xml") and ORIGIN + "/capabilities/" in rd("llms.txt") and '<link rel="canonical" href="' + ORIGIN + '/capabilities/"' in ch, "capabilities page: sitemap, llms, canonical")
    ok("VERIFIED<b>0</b>" in ch.replace("</div>", "") or ">VERIFIED<b>0<" in ch, "capabilities page: VERIFIED count shown as 0")
    # Dataset JSON-LD only on the genuine dataset page (#8 tranche 6)
    lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', ch, re.S)]
    dss = [x for x in lds if x.get("@type") == "Dataset"]
    ok(len(dss) == 1 and dss[0]["url"] == ORIGIN + "/capabilities/" and [d["contentUrl"] for d in dss[0]["distribution"]] == [ORIGIN + "/capabilities/index.json"]
       and str(cm["counts"]["total"]) in dss[0]["description"] and "license" not in dss[0] and "VERIFIED" not in dss[0]["description"].replace("Nothing is labelled VERIFIED", "").replace("nothing here is VERIFIED", ""), "capabilities page: one truthful Dataset JSON-LD pointing at index.json")
    dpages = [str(f.relative_to(s)) for f in s.rglob("*.html") if '"@type":"Dataset"' in f.read_text(errors="ignore")]
    ok(sorted(dpages) == ["capabilities/index.html", "trading/build/coverage/index.html"], f"Dataset JSON-LD only on the two dataset pages {dpages[:4]}")
    cvt = (s / "trading/build/coverage/index.html").read_text()
    cds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', cvt, re.S)]
    cds = [d for d in cds if d.get("@type") == "Dataset"]
    ok(len(cds) == 1 and cds[0]["url"] == ORIGIN + "/trading/build/coverage/" and [d["contentUrl"] for d in cds[0]["distribution"]] == [ORIGIN + "/trading/build/coverage.json", ORIGIN + "/trading/build/coverage.csv"] and "license" not in cds[0], "coverage page: one truthful Dataset JSON-LD pointing at coverage.json")
    # sitemaps: no gated URLs anywhere, txt == xml, legacy trading sitemap on public pages (#8 tranche 4)
    edge = s.parent / "netlify/edge-functions/free-session-gate.ts"
    if edge.exists():
        pl = re.search(r"path:\s*\[([^\]]*)\]", edge.read_text()).group(1)
        want = {x.rstrip("*") for x in re.findall(r'"([^"]+)"', pl)}
        ok(want == set(bd.GATED_PATHS), f"GATED_PATHS match the edge gate config {sorted(want ^ set(bd.GATED_PATHS))}")
    txt = [l.strip() for l in rd("sitemap.txt").splitlines() if l.strip()]
    ok(set(txt) == set(locs) and len(txt) == len(locs), "sitemap.txt has exactly the sitemap.xml URLs")
    tlocs = re.findall(r"<loc>([^<]+)</loc>", rd("trading/sitemap.xml"))
    ok(not [u for u in list(locs) + txt + tlocs if bd.is_gated(u)], "no gated URL in any sitemap")
    ok(tlocs and all(bd.url_to_file(s, u).exists() for u in tlocs), "trading/sitemap.xml URLs exist")
    ok(not [c["canonicalUrl"] for c in cm["capabilities"] if bd.is_gated(c["canonicalUrl"])], "capability canonical URLs are public pages")
    # trust facts re-read from the built pages
    for key, page, sent in bd.FACTS:
        ok(sent in bd.visible_text(s / page), f"trust fact {key} not on {page}")
    if a.live:
        L = a.live.rstrip("/")
        files = []
        for p in ["robots.txt", "sitemap.xml", "llms.txt", ".well-known/bsv-trust.json", ""]:
            st, body, h = get(f"{L}/{p}")
            ok(st == 200, f"live {p or '/'} {st}")
            files.append(body)
            if p.endswith(".json"):
                ok("json" in h.get("Content-Type", h.get("content-type", "")), "live trust.json content-type")
        check_text(tuple(files))
        live_m = json.loads(files[3])
        import html as H
        for key, page, sent in bd.FACTS:  # fresh read from production
            st, body, _ = get(f"{L}/{page}")
            t = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S | re.I))))
            ok(st == 200 and sent in t, f"live trust fact {key} not on {page}")
        for u in re.findall(r"https://botshelfvampire\.com/[^\s)]*", files[2].split(bd.LL_BEGIN, 1)[1]):
            st, _, _ = get(u.replace(ORIGIN, L))
            ok(st == 200, f"live llms link {u} {st}")
        # every sitemap / capability URL answers 200 to an anonymous visitor without a redirect
        from concurrent.futures import ThreadPoolExecutor
        urls = sorted(set(locs) | set(tlocs) | {c["canonicalUrl"] for c in cm["capabilities"]})
        with ThreadPoolExecutor(16) as ex:
            sts = list(ex.map(lambda u: status_no_redirect(u.replace(ORIGIN, L)), urls))
        badu = [(u, x) for u, x in zip(urls, sts) if x != 200]
        ok(not badu, f"live: {len(urls)} sitemap/capability URLs 200 without redirect; bad {badu[:5]}")
        for ua in ["OAI-SearchBot/1.0; +https://openai.com/searchbot", "Mozilla/5.0"]:
            st, _, _ = get(f"{L}/trading/build/", ua)
            ok(st == 200, f"live /trading/build/ for {ua} {st}")
        st, body, _ = get(f"{L}/.netlify/functions/demand-request?op=public")
        if st == 200:
            j = json.loads(body)
            ok(j.get("ok") is True and isinstance(j.get("requests"), list) and j["counts"]["published"] == len(j["requests"]), "live requests API: counts match listed rows")
            ok(all("user_id" not in r and "@" not in json.dumps(r) for r in j["requests"]), "live requests API: no user ids or emails")
            st3, cb, _ = get(f"{L}/capabilities/index.json")
            ok(st3 == 200 and json.loads(cb)["counts"] == cm["counts"], f"live capabilities/index.json {st3}")
            st4, sb, _ = get(f"{L}/.netlify/functions/demand-request?op=signals")
            if st4 == 200:
                sj = json.loads(sb)
                osc = json.loads((s / "schemas/opportunity-signal-v0.1.json").read_text())
                serr = [e for g in sj["signals"] for e in schema_errors(g, osc, g.get("signalId", "?"))]
                ok(not serr and sj["collected"]["NO_RESULT_SEARCH"] is False and "@" not in json.dumps(sj["signals"]), f"live signals: schema-valid, uncollected types off {serr[:3]}")
                ok(sum(g["count"] for g in sj["signals"]) == j["counts"]["published"], "live signals: counts add up to published requests")
            else:
                ok(False, f"live signals API {st4}")
            st5, fb, _ = get(f"{L}/.netlify/functions/demand-request?op=feed")
            try:
                import xml.etree.ElementTree as ET
                fr = ET.fromstring(fb.encode("utf-8")); ns = "{http://www.w3.org/2005/Atom}"
                ents = fr.findall(ns + "entry")
                ok(st5 == 200 and fr.tag == ns + "feed" and len(ents) == min(50, j["counts"]["published"]) and "@" not in fb, f"live Atom feed: parses, {len(ents)} entries = published requests, no emails")
            except Exception as e:
                ok(False, f"live Atom feed {st5}: {e}")
            st2, ob, _ = get(f"{L}/requests/opportunities.json")
            ok(st2 == 200 and json.loads(ob)["signals"]["noResultSearches"]["collected"] is False, f"live opportunities.json {st2}")
            st3, cb, _ = get(f"{L}/trading/build/coverage.json")
            ok(st3 == 200 and json.loads(cb)["counts"]["runtimeTestedByBSV"] == 0, f"live coverage.json {st3}")
        else:
            ok(False, f"live requests API {st}")
        st, _, _ = get(f"{L}/.netlify/functions/demand-request?op=queue")
        ok(st == 401, f"live requests queue anonymous -> 401 ({st})")
        st, body, _ = get(f"{L}/library/source/botshelf-deep-research-3b.html")
        ok(st in (301, 302, 303, 401, 403) or "BSV-GATED" in body, f"live gated source still gated ({st})")
    print(json.dumps({"checks": n, "failures": len(fails), "fail": fails[:20]}, ensure_ascii=False))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
