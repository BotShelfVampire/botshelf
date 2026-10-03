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
        ok(op["signals"]["noResultSearches"]["collected"] is False and op["signals"]["pageViews"]["collected"] is False, "opportunities: uncollected signals marked, not invented")
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
            st2, ob, _ = get(f"{L}/requests/opportunities.json")
            ok(st2 == 200 and json.loads(ob)["signals"]["noResultSearches"]["collected"] is False, f"live opportunities.json {st2}")
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
