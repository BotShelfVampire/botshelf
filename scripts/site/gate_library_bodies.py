#!/usr/bin/env python3
"""Move the full prompt/config/code body of the 70 existing Library team implementations
(/library/<runtime>/<team>/) behind the existing server-verified email session.

Public page keeps: title, summary, explanation sections, files list, example in/out, test status.
Gated page (/library/source/team-<runtime>-<team>.html, covered by the /library/source/* edge gate)
holds: the full body, copy button, GitHub source link, license.
Also strips `body` from the public /library/catalog/items.json and prunes build artifacts
(*.bak* backups and the library generator scripts) from the deploy tree.

Idempotent: a page that is already gated is left alone (its gated page must already exist).
Usage: python3 scripts/site/gate_library_bodies.py --site <production tree> [--packs skills,mcp|all]

Second phase (--packs): the ~809 Library pack items with a "Full FREE body" section get the same treatment,
gated at /library/source/item-<runtime>-<slug>.html.
"""
import argparse, html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402  (lib_shell, assets, esc)

MARK = 'data-bsv-gate="lib-body"'
SEC_RE = re.compile(r'<section class="how-box"><p class="section-label">Full prompt / config / code</p>.*?<pre class="lib-pre" id="lib-body">(.*?)</pre></section>', re.S)
# Provenance only: the registry repo is public (owner decision); the public page shows the path, not a "gated" claim.
GH_NOTE = '<span class="muted">(path in the BSV team registry repository)</span>'
OLD_GH_NOTE = '<span class="muted">(link shown after free email verification)</span>'
GH_RE = re.compile(r'<a href="(https://github\.com/BotShelfVampire/botshelf-ai-team-registry/[^"]+)" data-evt="github_source_open" rel="noopener">(<code>[^<]*</code>)</a>')


def gated_name(url: str) -> str:
    _, _, runtime, slug, _ = url.split("/")
    return f"team-{runtime}-{slug}"


def section_text(page: str, label: str) -> str:
    m = re.search(r'<section class="how-box"><p class="section-label">' + re.escape(label) + r'</p>(.*?)</section>', page, re.S)
    return m.group(1) if m else ""


PACK_RE = re.compile(r'<section class="how-box"><p class="section-label">Full FREE body</p>\s*<p class="btn-row">.*?(<a class="btn" href="(/library/[a-z0-9-]+/)">([^<]*)</a>)</p>\s*(<p class="muted lang-honesty"[^>]*>.*?</p>)?\s*<pre class="lib-pre" id="lib-body">(.*?)</pre></section>', re.S)
PACK_SKIP = {"toolkit", "teams", "source", "catalog", "registry"}


def pack_pages(site: Path, runtimes=None):
    out = []
    for pp in sorted(site.glob("library/*/*/index.html")):
        rt, slug = pp.parts[-3], pp.parts[-2]
        if rt in PACK_SKIP or (runtimes and rt not in runtimes):
            continue
        if not re.fullmatch(r"[a-z0-9-]+", rt + slug):
            raise SystemExit(f"unexpected slug {rt}/{slug}")
        out.append((rt, slug, pp))
    return out


def gate_packs(site: Path, runtimes=None) -> dict:
    """Library pack items (skills, kimi, gemini, deepseek, ...): 'Full FREE body' -> /library/source/item-<runtime>-<slug>.html"""
    done = skipped = other = 0
    for rt, slug, pp in pack_pages(site, runtimes):
        page = pp.read_text()
        name = f"item-{rt}-{slug}"
        gp = site / f"library/source/{name}.html"
        if MARK in page:
            if 'Full FREE body' in page and not gp.exists():
                raise SystemExit(f"{pp}: gated but {gp} missing")
            skipped += 1
            continue
        m = PACK_RE.search(page)
        if not m:
            if "Full FREE body" in page:
                raise SystemExit(f"{pp}: body section not parsed")
            other += 1
            continue
        back, back_href, back_label, honesty, pre_html = m.group(1), m.group(2), m.group(3), m.group(4) or "", m.group(5)
        title = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S).group(1)
        url = f"/library/{rt}/{slug}/"
        nxt = f"/library/source/{name}.html"
        body = (f'<p class="kicker"><a href="/library/">Library</a> · <a href="{back_href}">{back_label.replace("Back to ", "")}</a></p><h1>{title}</h1>'
                f'<p class="lib-meta"><span class="tk-badge">FREE</span></p>'
                f'<section class="section"><p class="section-label">Full FREE body</p><p><button type="button" class="btn" data-tk-copy="lib-body">Copy</button></p>{honesty}'
                f'<pre id="lib-body" tabindex="0">{pre_html}</pre></section><p><a href="{url}">← Explanation page</a></p>')
        blt.write(gp, blt.lib_shell(site, f"{html.unescape(re.sub(r'<[^>]+>', '', title))} — full text | BotShelf Vampire", "Full free body (email-verified).", url, body, robots="noindex,nofollow"))
        entry = (f'<section class="how-box" {MARK}><p class="section-label">Full FREE body</p>'
                 f'<p><strong>Free.</strong> The full text opens after free email verification — no payment. The explanation on this page stays public.</p>'
                 f'<p data-lang-show="ja" hidden><strong>無料です。</strong>全文は無料のメール確認後に表示されます（支払いは不要です）。このページの解説は登録なしで読めます。</p>'
                 f'<p class="btn-row"><a class="btn" href="{nxt}" data-evt="lib_body_gate_open">Open full text — free email verification</a> {back}</p>'
                 f'<p class="muted" data-lang-show="en">If you are sent to registration, verify your email and press this button again.</p>'
                 f'<p class="muted" data-lang-show="ja" hidden>登録画面に移動した場合は、メール確認を済ませてからもう一度このボタンを押してください。</p></section>')
        pp.write_text(page[:m.start()] + entry + page[m.end():], encoding="utf-8")
        done += 1
    return {"pack_gated_now": done, "pack_already_gated": skipped, "pack_without_body": other}


def prune(site: Path) -> int:
    pruned = 0
    for f in list(site.rglob("*")):
        rel = str(f.relative_to(site))
        if f.is_file() and not rel.startswith("node_modules/") and (".bak" in f.name or rel in ("library/build_library.py", "library/_phase3.py")):
            f.unlink(); pruned += 1
    return pruned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--packs", default="", help="comma-separated runtimes to gate in this batch, or 'all'")
    a = ap.parse_args()
    site = Path(a.site)
    blt.assets(site)
    pack_rep = {}
    if a.packs:
        pack_rep = gate_packs(site, None if a.packs == "all" else set(a.packs.split(",")))
    reg = json.loads((site / "library/registry.json").read_text())
    impls = [(t, i) for t in reg["teams"] for i in t["implementations"]]
    items_p = site / "library/catalog/items.json"
    items = json.loads(items_p.read_text())
    by_id = {x["implementation_id"]: x for x in items}
    done = skipped = 0
    for team, impl in impls:
        url = impl["url"]
        name = gated_name(url)
        pp = site / url.lstrip("/") / "index.html"
        page = pp.read_text()
        gp = site / f"library/source/{name}.html"
        if MARK in page:
            if not gp.exists():
                raise SystemExit(f"{url}: already gated but {gp} missing — rebuild from a fresh production tree")
            if OLD_GH_NOTE in page:  # migrate pages gated before the provenance wording changed
                pp.write_text(page.replace(OLD_GH_NOTE, GH_NOTE), encoding="utf-8")
            skipped += 1
            continue
        m = SEC_RE.search(page)
        if not m:
            raise SystemExit(f"{url}: body section not found")
        pre_html = m.group(1)
        it = by_id.get(impl["implementation_id"]) or {}
        if it.get("body") is not None and html.unescape(pre_html).strip() != str(it["body"]).strip():
            print(f"warn: {url} page body differs from items.json body; gating the page body", file=sys.stderr)
        title = re.search(r"<h1>(.*?)</h1>", page, re.S).group(1)
        gh = GH_RE.search(page)
        files = section_text(page, "Files")
        lic = it.get("license") or "free-use-at-own-risk"
        nxt = f"/library/source/{name}.html"
        # gated page
        body = (f'<p class="kicker"><a href="/library/">Library</a> · <a href="/library/{impl["url"].split("/")[2]}/">{blt.esc(impl.get("platform") or impl["url"].split("/")[2])}</a> · '
                f'<a href="/library/teams/{blt.esc(team["team_id"])}/">{blt.esc(team["title"])}</a></p><h1>{title}</h1>'
                f'<p class="lib-meta"><span class="tk-badge">FREE</span><span class="tk-badge">{blt.esc(impl.get("type") or "")}</span><span class="tk-badge tk-warn">{blt.esc(impl.get("status") or "")}</span></p>'
                f'<section class="section"><p class="section-label">Full prompt / config / code</p><p><button type="button" class="btn" data-tk-copy="lib-body">Copy</button></p>'
                f'<pre id="lib-body" tabindex="0">{pre_html}</pre></section>'
                + (f'<section class="section"><p class="section-label">Files</p>{files}</section>' if files else "")
                + (f'<section class="section"><p class="section-label">GitHub source</p><p><a href="{gh.group(1)}" rel="noopener">{gh.group(2)}</a> · license: <code>{blt.esc(lic)}</code></p></section>' if gh else
                   f'<section class="section"><p class="section-label">License</p><p><code>{blt.esc(lic)}</code></p></section>')
                + f'<p><a href="{url}">← Explanation page</a></p>')
        blt.write(gp, blt.lib_shell(site, f"{html.unescape(title)} — full text | BotShelf Vampire", f"Full prompt / config / code for {html.unescape(title)} (free, email-verified).", url, body, robots="noindex,nofollow"))
        # public page: replace body section with the gate entry; keep GitHub path as text only
        entry = (f'<section class="how-box" {MARK}><p class="section-label">Full prompt / config / code</p>'
                 f'<p><strong>Free.</strong> The full text opens after free email verification — no payment. The explanation, example input/output and file list on this page stay public.</p>'
                 f'<p data-lang-show="ja" hidden><strong>無料です。</strong>プロンプト・設定・コードの全文は、無料のメール確認後に表示されます（支払いは不要です）。このページの解説・入出力例・ファイル一覧は登録なしで読めます。</p>'
                 f'<p class="btn-row"><a class="btn" href="{nxt}" data-evt="lib_body_gate_open">Open full text — free email verification</a></p>'
                 f'<p class="muted" data-lang-show="ja" hidden>登録画面に移動した場合は、メール確認を済ませてからもう一度このボタンを押してください。</p>'
                 f'<p class="muted" data-lang-show="en">If you are sent to registration, verify your email and press this button again.</p></section>')
        page = page[:m.start()] + entry + page[m.end():]
        if gh:
            page = page.replace(gh.group(0), gh.group(2) + ' ' + GH_NOTE, 1)
        pp.write_text(page, encoding="utf-8")
        done += 1
    # public catalog JSON: no bodies
    changed = 0
    for x in items:
        if "body" in x:
            x.pop("body")
            changed += 1
        x["body_gated"] = True
        x["body_url"] = f"/library/source/{gated_name('/library/' + x['implementation_id'] + '/')}.html"
    items_p.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # build artifacts are not site content: *.bak* backups (some hold gated pages) and the library generators (they embed bodies)
    pruned = prune(site)
    print(json.dumps(dict({"implementations": len(impls), "gated_now": done, "already_gated": skipped, "items_json_bodies_removed": changed, "artifacts_pruned": pruned}, **pack_rep)))


if __name__ == "__main__":
    main()
