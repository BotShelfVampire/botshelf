#!/usr/bin/env python3
"""Issue #8 tranche 3: machine-readable capability manifests (capability-manifest v0.1) for every public catalogue
entry and every BSV recipe, so agents can search BSV without scraping card prose.

Every field is derived from public files at build time (/trading/catalog.json, trader-toolkit recipes, generator
targets); nothing is estimated. Verification follows the catalogue flags: no entry is VERIFIED, because BSV has not
compiled or run any of them on their platforms. Writes /capabilities/index.json and publishes the schema at its $id
URL (/schemas/capability-manifest-v0.1.json, byte-identical to schemas/bsv-capability-manifest.schema.json)."""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ORIGIN = "https://botshelfvampire.com"
SCHEMA_URL = ORIGIN + "/schemas/capability-manifest-v0.1.json"
SPDX = "https://spdx.org/licenses/{}.html"

SIDE = {
    "Expert Advisor": (["Can open, modify and close orders on the trading account it is attached to."],
                       ["The user attaches it to a chart and enables automated trading in the platform; test on a demo account first."]),
    "Trade manager": (["Can modify or close orders and positions on the trading account it is attached to."],
                      ["The user attaches it to a chart and enables automated trading in the platform; test on a demo account first."]),
    "Strategy": (["Generates strategy orders inside the platform's strategy engine or tester."],
                 ["The user adds it to a chart and decides whether any order is routed to an account."]),
}
DEFAULT_SIDE = ([], ["The user adds it to a chart; read the source before running it."])
OUTPUTS = {"Indicator": "chart plots and alerts", "Expert Advisor": "orders and position management", "Trade manager": "order and position management",
           "Strategy": "strategy orders and backtest results", "Script": "one-off chart script output", "Template": "chart template"}


def canonical(site: Path, rel: str) -> str:
    p = site / rel
    if p.exists():
        m = re.search(r'<link rel="canonical" href="([^"]+)"', p.read_text(errors="ignore"))
        if m:
            return m.group(1)
    return ORIGIN + "/" + rel


def public_page(site: Path, i: dict) -> str:
    """/trading/items/* is gated by the edge (anonymous visitors are redirected to /trading/tools/<id>.html), so the
    public description page is the canonical URL for agents."""
    tool = f"trading/tools/{Path(i['detail_url']).name}"
    return canonical(site, tool if (site / tool).exists() else "trading/" + i["detail_url"])


def license_of(site: Path, item: dict) -> dict:
    lf = item.get("license_file")
    if lf and (site / "trading/licenses" / Path(lf).name.lower()).exists():
        url = f"{ORIGIN}/trading/licenses/{Path(lf).name.lower()}"
    elif item.get("license_url"):
        url = item["license_url"]
    else:
        url = SPDX.format(item["license"])
    return {"label": item["license"], "url": url}


def catalogue_manifest(site: Path, i: dict) -> dict:
    side, approval = SIDE.get(i["kind"], DEFAULT_SIDE)
    if i.get("runtime_tested") is True:
        status = "PARTIAL"
    elif i.get("compiled") is True:
        status = "STRUCTURAL"
    else:
        status = "UNTESTED"
    ev = ["Compiled by BSV: " + ("yes" if i.get("compiled") else "no") + "; runtime-tested by BSV: " + ("yes" if i.get("runtime_tested") else "no") + "."]
    if i.get("distribution") == "bundled":
        ev.append(f"Original bytes and file-level license checked against the pinned commit {i['commit'][:12]} (provenance only, not a functional test).")
    else:
        at = f" at commit {i['commit'][:12]}" if i.get("commit") else (f" (branch {i['branch']})" if i.get("branch") else "")
        ev.append(f"Author-hosted: links to the author's source{at}; BSV does not redistribute it.")
    ev.append("Catalogue risk label: " + i["risk_level"] + "; checked " + i["check_date"] + ".")
    return {
        "schemaVersion": "0.1",
        "capabilityId": "trading." + i["id"],
        "title": i["name"][:120],
        "job": i["text"]["en"]["purpose"][:500],
        "domains": ["trading", i["category"].lower()],
        "inputs": [{"name": "chart bars", "type": "OHLCV price series"}],
        "outputs": [{"name": OUTPUTS.get(i["kind"], i["kind"].lower()), "type": i["kind"]}],
        "runtime": {"platform": " / ".join(i["platforms"]), "version": None, "requirements": [f"{p} with the user's own account" for p in i["platforms"]]},
        "permissions": [],
        "dataSensitivity": "public",
        "sideEffects": side,
        "approvalBoundary": approval,
        "verification": {"status": status, "evidence": ev},
        "license": license_of(site, i),
        "seller": {"id": "github:" + i["repo"].split("/")[0], "displayName": i["provider"]},
        "dependencies": [],
        "monetization": {"mode": "FREE", "price": None, "currency": None},
        "canonicalUrl": public_page(site, i),
    }


def recipe_manifest(site: Path, stem: str, r: dict, targets: list, checks: list) -> dict:
    return {
        "schemaVersion": "0.1",
        "capabilityId": "bsv.recipe." + stem,
        "title": r["name"][:120],
        "job": (r.get("description") or r["name"])[:500],
        "domains": ["trading", "chart-tools"],
        "inputs": [{"name": "chart bars", "type": "OHLCV price series"}, {"name": "recipe JSON", "type": "bsv-trader-recipe v" + str(r.get("schemaVersion", "0.1"))}],
        "outputs": [{"name": f"starter source for {len(targets)} platforms", "type": "source code"}],
        "runtime": {"platform": "BSV recipe generator", "version": None, "requirements": targets},
        "permissions": [],
        "dataSensitivity": "public",
        "sideEffects": ["The generated starters are indicators or studies that plot and raise alerts; none is written to place orders."],
        "approvalBoundary": ["The user pastes a starter into their own platform, compiles it there and decides whether to use it."],
        "verification": {"status": "STRUCTURAL", "evidence": ["Structure reviewed — not runtime tested (recipe page label)."] + checks},
        "license": {"label": "MIT", "url": SPDX.format("MIT")},
        "seller": {"id": "bsv", "displayName": "BotShelf Vampire (original BSV source)"},
        "dependencies": [],
        "monetization": {"mode": "FREE", "price": None, "currency": None},
        "canonicalUrl": canonical(site, f"trading/items/bsv-recipe-{stem}.html"),
    }


CHECKS = ["BSV parity test: builder output equals the CLI generator for every recipe and target.",
          "BSV target checks (stub compiles, subset parsers/evaluators, node:vm stubs) — BSV's own checks, not runs on the platforms."]


def build(site: Path) -> dict:
    cat = json.loads((site / "trading/catalog.json").read_text())
    tk = json.loads((REPO / "trader-toolkit/catalog.json").read_text())
    targets = [label for _, label, _ in blt.TARGETS]
    caps = [catalogue_manifest(site, i) for i in cat]
    for stem in tk["recipes"]:
        r = json.loads((REPO / f"trader-toolkit/recipes/{stem}.json").read_text())
        caps.append(recipe_manifest(site, stem, r, targets, CHECKS))
    teleop = 0
    for rel in sorted((site / "robot-pilot/teleop-recipes").glob("*.json")) if (site / "robot-pilot/teleop-recipes").exists() else []:
        r = json.loads(rel.read_text())
        caps.append({
            "schemaVersion": "0.1", "capabilityId": "bsv.teleop-recipe." + r["recipeId"].removeprefix("bsv-teleop-"),
            "title": r["title"][:120], "job": "Run and document a simulation teleoperation practice session: SOP, reset, failure taxonomy, acceptance criteria, export map and replay checklist.",
            "domains": ["robotics", "teleoperation"],
            "inputs": [{"name": "simulation session", "type": "operator practice"}],
            "outputs": [{"name": "labelled episodes and session evidence", "type": "teleop-session-evidence v0.1"}],
            "runtime": {"platform": "NVIDIA Isaac Lab + Isaac Teleop (simulation)", "version": None, "requirements": ["Follow NVIDIA's current official install instructions", "Simulation only"]},
            "permissions": [], "dataSensitivity": "public", "sideEffects": [],
            "approvalBoundary": ["Simulation only; any real-hardware use needs the hardware owner's own authorization."],
            "verification": {"status": "UNTESTED", "evidence": [r["statusNote"]]},
            "license": {"label": r["license"], "url": SPDX.format(r["license"])},
            "seller": {"id": "bsv", "displayName": "BotShelf Vampire (original BSV source)"},
            "dependencies": [ORIGIN + "/robot-pilot/curricula/isaac-teleop-so101-sim-v1.json"],
            "monetization": {"mode": "FREE", "price": None, "currency": None},
            "canonicalUrl": canonical(site, "robot-pilot/index.html"),
        })
        teleop += 1
    ids = [c["capabilityId"] for c in caps]
    if len(set(ids)) != len(ids):
        raise SystemExit("capabilities: duplicate ids")
    status = {}
    for c in caps:
        status[c["verification"]["status"]] = status.get(c["verification"]["status"], 0) + 1
    out = {
        "schemaVersion": "0.1",
        "manifestSchema": SCHEMA_URL,
        "sources": [ORIGIN + "/trading/catalog.json", "trader-toolkit/catalog.json (recipes) in the BSV repository", ORIGIN + "/robot-pilot/#recipes"],
        "method": "Generated at build time from the public catalogue and the BSV recipes. Verification follows the catalogue flags; nothing here is VERIFIED because BSV has not run these on their platforms. Gated source is not included.",
        "counts": {"total": len(caps), "catalogue": len(cat), "bsvRecipes": len(tk["recipes"]), "teleopRecipes": teleop, "byVerificationStatus": dict(sorted(status.items()))},
        "capabilities": caps,
    }
    d = site / "capabilities"
    d.mkdir(exist_ok=True)
    (d / "index.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    sd = site / "schemas"
    sd.mkdir(exist_ok=True)
    (sd / "capability-manifest-v0.1.json").write_text((REPO / "schemas/bsv-capability-manifest.schema.json").read_text())
    (d / "index.html").write_text(page(site, out))
    smp = site / "sitemap.xml"; sm = smp.read_text(); u = ORIGIN + "/capabilities/"
    if f"<loc>{u}</loc>" not in sm:
        smp.write_text(sm.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>2026-10-04</lastmod></url>\n</urlset>"))
    return {"capabilities": len(caps), "by_status": out["counts"]["byVerificationStatus"], "page": "/capabilities/"}


def page(site: Path, out: dict) -> str:
    """Human-readable list of the same manifests as /capabilities/index.json (Issue #8 tranche 5). Static HTML, no
    script: every row and count is read from `out`; nothing is added or upgraded."""
    from build_request_market import both
    if "tcss" not in blt.ASSET:
        blt.assets(site)
    esc = blt.esc
    c = out["counts"]
    cj = json.loads((site / "trading/catalog.json").read_text()); cj = cj if isinstance(cj, list) else cj.get("items", [])
    rt = sum(1 for i in cj if isinstance(i, dict) and i.get("runtime_tested") is True)  # counted, not typed in
    groups = [("catalogue", "Traders Library catalogue", "Traders Library カタログ", lambda x: x["capabilityId"].startswith("trading.")),
              ("recipes", "BSV recipes (generator)", "BSVレシピ（ジェネレーター）", lambda x: x["capabilityId"].startswith("bsv.recipe.")),
              ("teleop", "Teleop recipes", "遠隔操作レシピ", lambda x: x["capabilityId"].startswith("bsv.teleop-recipe."))]
    def row(x):
        url = x.get("canonicalUrl") or ""
        title = f'<a href="{esc(url)}">{esc(x["title"])}</a>' if url.startswith(ORIGIN + "/") else esc(x["title"])
        return (f'<tr id="{esc(x["capabilityId"])}"><td>{title}<div class="small muted">{esc(x["job"])}</div></td><td>{esc(x["runtime"]["platform"])}</td>'
                f'<td><code>{esc(x["verification"]["status"])}</code></td><td class="small">{esc((x.get("license") or {}).get("label") or "—")}</td>'
                f'<td class="small">{esc((x.get("monetization") or {}).get("mode") or "—")}</td></tr>')
    secs, chips = "", ""
    for gid, en, ja, f in groups:
        rows = [x for x in out["capabilities"] if f(x)]
        if not rows:
            continue
        chips += f'<a class="chip" href="#{gid}">{both(en, ja)} ({len(rows)})</a>'
        secs += (f'<section class="container bb-section" id="{gid}"><h2>{both(en, ja)} <span class="small muted">({len(rows)})</span></h2>'
                 f'<div class="bb-table-wrap"><table class="qa-table"><thead><tr><th>{both("Capability", "機能")}</th><th>{both("Runtime", "実行環境")}</th>'
                 f'<th>{both("Verification", "検証")}</th><th>{both("License", "ライセンス")}</th><th>{both("Access", "提供")}</th></tr></thead><tbody>'
                 + "".join(row(x) for x in rows) + '</tbody></table></div></section>')
    st = " · ".join(f"<code>{esc(k)}</code> {v}" for k, v in c["byVerificationStatus"].items())
    body = (
        '<section class="container hero bb-hero"><div><div class="eyebrow">CAPABILITY MANIFESTS</div>'
        f'<h1>{both("What each tool does, what it needs, and what was actually checked.", "それぞれのツールが何をし、何が必要で、実際に何を確認したか。")}</h1>'
        f'<p>{both("The same records as /capabilities/index.json (capability-manifest v0.1), as a readable list. Verification is shown exactly as labelled.", "/capabilities/index.json（capability-manifest v0.1）と同じ記録を、読みやすい一覧にしたものです。検証の状態は表示どおりそのままです。")}</p>'
        f'<p class="small"><q>{esc(out["method"])}</q></p>'
        f'<p class="small"><a href="/capabilities/index.json">index.json</a> · <a href="/schemas/capability-manifest-v0.1.json">schema v0.1</a> · <a href="/transparency/#labels">{both("What the labels mean", "表示の意味")}</a></p>'
        '</div><aside class="hero-stats"><div class="stat-lines">'
        f'<div>{both("Manifests", "記録の数")}<b>{c["total"]}</b></div>'
        f'<div>VERIFIED<b>{c["byVerificationStatus"].get("VERIFIED", 0)}</b></div>'
        f'<div>{both("Runtime-tested by BSV", "BSVでの実行検証済み")}<b>{rt}</b></div>'
        '</div></aside></section>'
        f'<div class="container subnav">{chips}</div>'
        f'<section class="container bb-section"><p class="small">{both("By verification status", "検証の状態ごと")}: {st}</p>'
        f'<p class="small muted">{both("Gated source is not included. Links go to public pages only.", "メール確認が必要なソースは含めていません。リンク先は公開ページだけです。")}</p></section>'
        + secs
    )
    return blt.trader_shell(site, "Capability manifests — what each tool does and what was checked · BotShelf Vampire",
                            f"{c['total']} capability manifests: job, inputs, runtime, license and verification status for every public catalogue entry and BSV recipe." + (" Nothing is labelled VERIFIED." if not c["byVerificationStatus"].get("VERIFIED") else ""),
                            "/capabilities/", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    a = ap.parse_args()
    print(json.dumps(build(Path(a.site))))


if __name__ == "__main__":
    main()
