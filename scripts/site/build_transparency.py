#!/usr/bin/env python3
"""Issue #8 tranche 2: Transparency Center (/transparency/) — real figures only (idempotent).

Every rule is the exact sentence on a production page (build_discovery.FACTS; the build fails if one is missing).
Figures are counted at build time from public files (/trading/catalog.json, /trading/build/ cards, builder tabs) or
read live in the browser from aggregate-count APIs (Request Market, practice records). Nothing is estimated.
Sales and payout totals are not published (no public source yet) and the page says so.
"""
import argparse, collections, json, re, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import build_live_toolkit as blt
import build_discovery as bd
from build_request_market import both, h8

ORIGIN = bd.ORIGIN
JS = r"""(function(){'use strict';
function set(id,v){var e=document.getElementById(id);if(e)e.textContent=String(v)}
function get(u,f){fetch(u,{credentials:'omit'}).then(function(r){return r.json()}).then(function(j){if(j&&j.ok)f(j.counts||{})}).catch(function(){})}
document.addEventListener('DOMContentLoaded',function(){
 get('/.netlify/functions/demand-request?op=public',function(c){set('tc-rq-received',c.received||0);set('tc-rq-published',c.published||0)});
 get('/.netlify/functions/pilot-record?op=stats',function(c){set('tc-rp-received',c.received||0);set('tc-rp-reviewed',c.reviewed||0)});
});})();
"""
CHANGES = [  # material public changes, dated (JST), from this branch's LIVE deploys
    ("2026-10-04", "Trader Tool Blocks: visual.zone drawn on Tradovate when its source is a pivot (two lines, the last confirmed pivot high and low), checked against a reference on every bar in BSV's stub of the documented API; range zones stay TODO there. Not run on Tradovate (UNTESTED_RUNTIME).", "/trading/build/"),
    ("2026-10-04", "Capability manifests now include the AI toolkit: one record per AI toolkit entry, all labelled UNTESTED with the catalog status quoted; BSV has not run any of them.", "/capabilities/#ai"),
    ("2026-10-04", "AI toolkit pages get an \"Ask for another framework\" link and each Robot Pilot curriculum module gets a mission-request link; the request form opens with the item named and sends nothing until you press send with a verified email.", "/requests/#rq-form"),
    ("2026-10-04", "AI toolkits: the AI Team Handoff Packet source page (free email verification) gets a checker for a filled packet that applies the packet's own rules in the browser; nothing is uploaded, and it checks structure and wording, not whether the facts are true.", "/library/toolkit/ai-team-handoff/"),
    ("2026-10-04", "Tradovate starters now compute pivots, liquidity sweep candidates and regular divergence from closed bars (per-bar state, unchanged by forming-bar updates), checked against BSV's own reference in a stub of the documented API. Not run in Tradovate.", "/trading/build/coverage/"),
    ("2026-10-04", "AI toolkits: the AI Team Handoff Packet (framework-neutral plain-text template for handing a job between AI workers or human reviewers) added; source prepared, not runtime tested; source behind free email verification.", "/library/toolkit/ai-team-handoff/"),
    ("2026-10-04", "This list is also published as JSON (/transparency/changes.json) and as an Atom feed; the request form offers the builder's trading platforms as tap-to-add picks; the practice log can be backed up as one JSON file and re-imported (kept in the browser, nothing uploaded).", "/transparency/changes.json"),
    ("2026-10-04", "Liquidity sweep candidates (signal.liquidity_sweep) and regular divergence (signal.divergence) rendered on backtrader, Backtesting.py and NautilusTrader, checked bar by bar against an independent reference with a no-lookahead prefix test. Candidates only; not run on a broker or live feed.", "/trading/build/coverage/"),
    ("2026-10-04", "thinkorswim (thinkScript) now reads the last closed higher-timeframe bar (secondary aggregation with [1] taken in that aggregation, never mixed with chart prices); BSV's thinkScript-subset evaluator models secondary contexts, compares with an hourly reference and checks it never looks ahead. Not run in thinkorswim.", "/trading/build/coverage/"),
    ("2026-10-04", "AmiBroker (AFL) now reads the last closed higher-timeframe bar (TimeFrameSet + Ref(x, -1) + TimeFrameExpand expandFirst, as the AFL guide advises for trading rules); BSV's AFL-subset evaluator compares it with an hourly reference and checks it never looks ahead. Not run in AmiBroker.", "/trading/build/coverage/"),
    ("2026-10-04", "cTrader (C#) now reads the last closed higher-timeframe bar (MarketData.GetBars + GetIndexByTime stepped back, minus 1; at most one extra bar of lag, never a forming bar) and the cTrader output compiles against BSV stubs from the API reference. Not run on cTrader.", "/trading/build/coverage/"),
    ("2026-10-04", "Coverage TODO matrix also as CSV (coverage.csv), official higher-timeframe doc links per target; each generator gap on the requests page has an ask-for-it link; Robot Pilot practice log can import saved session-evidence files (checked against the schema, in the browser only).", "/trading/build/coverage/"),
    ("2026-10-04", "Pivots (structure.pivot), zones (visual.zone) and webhook payloads (alert.webhook, printed and never sent) rendered on backtrader, Backtesting.py and NautilusTrader, checked bar by bar.", "/trading/build/coverage/"),
    ("2026-10-04", "Higher timeframe on Pine v6, MQL5, MQL4 and NinjaTrader 8: the last closed higher-timeframe bar through each platform's officially documented idiom (statically checked by BSV, not run: UNTESTED_RUNTIME) instead of a TODO stub.", "/trading/build/coverage/"),
    ("2026-10-04", "Readable generator coverage page (the BSV check behind each target, TODO matrix); generator gaps name the targets that render each block; practice log downloadable as CSV.", "/trading/build/coverage/"),
    ("2026-10-04", "Ranges and breakouts (structure.range, signal.breakout) rendered on backtrader, Backtesting.py and NautilusTrader; Opening Range and Session Stats panels complete there.", "/trading/build/"),
    ("2026-10-04", "Correction: higher-timeframe blocks were computed on the chart timeframe on every target. Now real (closed bars only) on backtrader, Backtesting.py and NautilusTrader; TODO stubs on the other 19.", "/trading/build/coverage.json"),
    ("2026-10-04", "Teleop recipe library: an original SO-101 simulation practice-session recipe (not run by BSV).", "/robot-pilot/#recipes"),
    ("2026-10-04", "Builder opportunity signals (opportunity-signal v0.1) counted from approved public requests only.", "/requests/#builders"),
    ("2026-10-04", "Capability manifests (capability-manifest v0.1) for every public catalogue entry and BSV recipe; nothing marked VERIFIED.", "/capabilities/index.json"),
    ("2026-10-04", "Readable capability manifest list; request permalinks and area filter; in-browser check of saved practice files.", "/capabilities/"),
    ("2026-10-04", "Generator coverage file: which BSV check covers each of the 22 targets, and TODO lines per recipe and target (none runtime-tested by BSV).", "/trading/build/coverage.json"),
    ("2026-10-04", "Demand heatmap (area × platform) on the Request Market, counted from open public requests only.", "/requests/#heatmap"),
    ("2026-10-04", "Robot Pilot Academy: tooling gaps for engineers, listing what the BSV teleop material covers and leaves out.", "/robot-pilot/#tooling"),
    ("2026-10-04", "Value panels (visual.table) rendered on 6 of 22 targets where a BSV check covers them; the rest stay TODO.", "/trading/build/"),
    ("2026-10-04", "NautilusTrader (Python) starters listed; 22 builder targets.", "/trading/build/"),
    ("2026-10-04", "Backtesting.py (Python) starters listed; 21 builder targets.", "/trading/build/"),
    ("2026-10-04", "Request Market Atom feed of approved public requests; robot-pilot open missions board (real approved requests only).", "/requests/"),
    ("2026-10-04", "backtrader (Python) starters listed; 20 builder targets.", "/trading/build/"),
    ("2026-10-04", "Tradovate (JavaScript custom indicator) starters listed; 19 builder targets.", "/trading/build/"),
    ("2026-10-04", "Request Market builder view: live request counts by area and catalogue gaps (no estimates).", "/requests/#builders"),
    ("2026-10-04", "Transparency Center published (quoted rules and counted figures only).", "/transparency/"),
    ("2026-10-04", "Robot Pilot practice records can be sent for private review (self-reported; never a licence or certification).", "/robot-pilot/"),
    ("2026-10-04", "Robot Pilot Academy (simulation-first curriculum, browser practice record, mission requests).", "/robot-pilot/"),
    ("2026-10-03", "Request Market: verified-email requests, reviewed before listing; counts read from the store.", "/requests/"),
    ("2026-10-03", "Machine-readable trust facts at /.well-known/bsv-trust.json; robots.txt allows OAI-SearchBot and disallows GPTBot.", "/.well-known/bsv-trust.json"),
    ("2026-10-03", "AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python) and Backtesting.py (Python) starters listed; 18 builder targets.", "/trading/build/"),
]


def fact(key):
    for k, page, sent in bd.FACTS:
        if k == key:
            return page, sent
    raise KeyError(key)


def q(key):
    page, sent = fact(key)
    return f'<li><q>{blt.esc(sent)}</q> <a class="small" href="/{page}">{blt.esc(page)}</a></li>'


def figures(site: Path) -> dict:
    cat = json.loads((site / "trading/catalog.json").read_text())
    build = (site / "trading/build/index.html").read_text()
    status = collections.Counter(re.findall(r'class="bb-card" [^>]*data-status="([A-Z_]+)"', build))
    bh = (site / "trading/items/bsv-builder.html").read_text()
    tabs = re.findall(r'<button type="button" class="btn small-btn" data-rb-target="[a-z0-9-]+" aria-pressed="(?:true|false)">([^<]+)</button>', bh)
    return {"cat_total": len(cat), "cat_bundled": sum(1 for i in cat if i.get("distribution") == "bundled"),
            "cat_hosted": sum(1 for i in cat if i.get("distribution") == "author-hosted"),
            "cat_compiled": sum(1 for i in cat if i.get("compiled") is True), "cat_runtime": sum(1 for i in cat if i.get("runtime_tested") is True),
            "build_total": sum(status.values()), "build_status": dict(sorted(status.items())), "targets": [blt.html.unescape(t) if hasattr(blt, "html") else t for t in tabs]}


def change_feeds(today):
    """The same dated list as section 7, as JSON and as an Atom feed (dates are JST; entry ids are stable)."""
    import hashlib
    from xml.sax.saxutils import escape as xe
    rows = [{"date": d, "text": t, "url": ORIGIN + u, "id": "tag:botshelfvampire.com," + d + ":changes/" + hashlib.sha1((d + "\n" + t).encode()).hexdigest()[:12]} for d, t, u in CHANGES]
    j = {"name": "BotShelf Vampire: recent material public changes", "page": ORIGIN + "/transparency/#changes", "dates": "Asia/Tokyo (JST), date only",
         "note": "The same list as section 7 of the Transparency Center, newest first. Each line describes a change that is live on the site; checks named there are BSV's own checks, not runs on the platforms.",
         "built": today, "count": len(rows), "changes": rows}
    upd = (max(d for d, _, _ in CHANGES) if CHANGES else today) + "T00:00:00+09:00"
    a = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
         '<title>BotShelf Vampire: recent material public changes</title>', f'<id>{ORIGIN}/transparency/changes.atom</id>',
         f'<link rel="self" type="application/atom+xml" href="{ORIGIN}/transparency/changes.atom"/>', f'<link rel="alternate" type="text/html" href="{ORIGIN}/transparency/#changes"/>',
         f'<updated>{upd}</updated>', '<author><name>BotShelf Vampire</name><email>support@botshelfvampire.com</email></author>']
    for r in rows:
        a += ['<entry>', f'<id>{r["id"]}</id>', f'<title>{xe(r["text"][:120] + ("…" if len(r["text"]) > 120 else ""))}</title>', f'<updated>{r["date"]}T00:00:00+09:00</updated>',
              f'<link rel="alternate" type="text/html" href="{xe(r["url"])}"/>', f'<summary>{xe(r["text"])}</summary>', '</entry>']
    a.append('</feed>')
    return json.dumps(j, ensure_ascii=False, indent=1) + "\n", "\n".join(a) + "\n"


def page(site, F, css_href, js_href, today):
    for k, page_, sent in bd.FACTS:
        if sent not in bd.visible_text(site / page_):
            sys.exit(f"transparency: production sentence missing: {k} on {page_}")
    st = "".join(f"<li><code>{blt.esc(k)}</code>: {v}</li>" for k, v in F["build_status"].items())
    tg = "".join(f"<li>{blt.esc(t)}</li>" for t in F["targets"])
    ch = "".join(f'<li>{d}: {blt.esc(t)} <a class="small" href="{u}">{blt.esc(u)}</a></li>' for d, t, u in CHANGES)
    def sec(id_, en, ja, inner):
        return f'<section class="container bb-section" id="{id_}"><h2>{both(en, ja)}</h2>{inner}</section>'
    body = (
        '<section class="container hero bb-hero"><div><div class="eyebrow">TRANSPARENCY CENTER</div>'
        f'<h1>{both("How BotShelf Vampire works, in checkable facts.", "BotShelf Vampire の仕組みを、確かめられる事実で。")}</h1>'
        f'{both("Each rule below is quoted word for word from the production page it links to. Each figure is counted from a public file at build time or read live from an aggregate-count API. Nothing here is estimated.", "以下のルールは、リンク先の本番ページの文をそのまま引用しています。数字は、公開ファイルからビルド時に数えたもの、または集計APIからその場で読んだものです。推計はありません。", "p", "lead")}'
        f'<p class="small">{both("Built", "作成日")}: {today} · <a href="/.well-known/bsv-trust.json">bsv-trust.json</a> · <a href="/capabilities/index.json">capability manifests</a></p>'
        '</div><aside class="hero-stats"><div class="stat-lines">'
        f'<div>{both("Traders Library entries", "Traders Library の件数")}<b>{F["cat_total"]}</b></div>'
        f'<div>{both("Builder targets", "ビルダーの出力先")}<b>{len(F["targets"])}</b></div>'
        f'<div>{both("Runtime-tested by BSV", "BSVでの実行検証済み")}<b>{F["cat_runtime"]}</b></div>'
        '</div></aside></section>'
        + sec("money", "1. How BSV makes money", "1. BSVの収入", f'<ul>{q("seller_split_payout")}{q("ib_link_fee")}</ul><p class="small">{both("Fee types listed here are the ones stated on the production pages.", "ここに載せた料金は、本番ページに書かれているものです。")}</p>')
        + sec("buyers", "2. How buyer access works", "2. 購入者のアクセス", f'<ul>{q("payments")}{q("free_access")}{q("paid_access_start")}{q("paid_access_expiry")}{q("refunds")}</ul>')
        + sec("payouts", "3. How seller payouts work", "3. 出品者への支払い", f'<ul>{q("seller_split_payout")}{q("payout_network")}{q("price_floor")}{q("payout_holds")}{q("payout_hold_reason")}{q("no_private_key")}</ul>')
        + sec("labels", "4. Verification labels", "4. 検証の表示", f'<p>{both("Build assets on /trading/build/ by label (counted from the page):", "/trading/build/ の素材の表示ごとの数（ページから数えた値）:")} {F["build_total"]}</p><ul>{st}</ul>'
              f'<p>{both("Traders Library (counted from /trading/catalog.json):", "Traders Library（/trading/catalog.json から数えた値）:")} {F["cat_total"]} · bundled {F["cat_bundled"]} · author-hosted {F["cat_hosted"]} · compiled by BSV {F["cat_compiled"]} · runtime-tested by BSV {F["cat_runtime"]}</p>'
              f'<p class="small">{both("A label states exactly what was checked. Checks written by BSV (for example a language-subset parser) are not the platform vendor's compiler or a run on the platform.", "表示は確認した範囲そのものです。BSVが書いた検査（言語の一部を解釈する検査など）は、各社のコンパイラーやプラットフォーム上での実行ではありません。")}</p>')
        + sec("coverage", "5. Current platform / runtime coverage", "5. 対応しているプラットフォーム", f'<p>{both("Recipe builder targets (from the builder):", "レシピビルダーの出力先（ビルダーから取得）:")} {len(F["targets"])}</p><ul class="small bb-tags">{tg}</ul>')
        + sec("limits", "6. Known limitations", "6. わかっている制約", '<ul>'
              f'<li>{both("Runtime-tested by BSV", "BSVでの実行検証済み")}: {F["cat_runtime"]}. {both("Generated starters are prepared source, not runtime-verified tools.", "生成したコードは用意したソースであり、実行検証済みのツールではありません。")}</li>'
              f'<li>{both("Sales and payout totals are not published here yet; there is no public source for them on this site.", "売上と支払いの合計はまだ載せていません。このサイトに公開の元データがないためです。")}</li>'
              f'<li>{both("Request Market counts and practice-record counts are what users sent; requests and records are self-reported.", "Request Market と練習記録の数は、利用者が送ったものです。リクエストと記録は自己申告です。")}</li></ul>'
              f'<div class="rq-counts"><div>{both("Requests received", "受け付けたリクエスト")}<b id="tc-rq-received">–</b></div><div>{both("Requests listed", "公開中のリクエスト")}<b id="tc-rq-published">–</b></div>'
              f'<div>{both("Practice records received", "受け付けた練習記録")}<b id="tc-rp-received">–</b></div><div>{both("Looked at by a BSV reviewer", "BSVの確認担当が確認")}<b id="tc-rp-reviewed">–</b></div></div>')
        + sec("changes", "7. Recent material changes", "7. 最近の大きな変更", f'<ul>{ch}</ul><p class="small">{both("The same list, machine-readable:", "同じ一覧（機械可読）:")} <a href="/transparency/changes.json">changes.json</a> · <a href="/transparency/changes.atom">{both("Atom feed", "Atomフィード")}</a></p>')
        + sec("incidents", "8. Incident history", "8. 障害の履歴", f'<p>{both("No incident records are published yet. An incident is added here only after its facts (start, end, affected surface, impact, cause, fix) are verified.", "障害の記録はまだ載せていません。開始・終了・影響範囲・影響・原因・対応の事実を確かめてから載せます。")}</p>')
        + sec("support", "9. Support and dispute path", "9. 問い合わせ・異議", f'<ul>{q("support_email")}{q("refunds")}{q("payout_hold_reason")}</ul>')
        + sec("privacy", "10. Privacy: what BSV does and does not publish", "10. プライバシー: BSVが公開するもの・しないもの", f'<ul>{q("public_contact")}'
              f'<li>{both("Request Market: the account email is never shown; private requests are never listed.", "Request Market: アカウントのメールアドレスは表示しません。非公開のリクエストは表示しません。")} <a class="small" href="/requests/">/requests/</a></li>'
              f'<li>{both("Practice records: stored privately; only aggregate counts are public.", "練習記録: 非公開で保存し、公開するのは合計の数だけです。")} <a class="small" href="/robot-pilot/">/robot-pilot/</a></li>'
              f'<li><a href="/privacy.html">privacy.html</a></li></ul>')
    )
    h = blt.trader_shell(site, "Transparency Center — rules and figures you can check · BotShelf Vampire",
                         "How BotShelf Vampire works: buyer access, seller payouts, fees, verification labels and coverage, quoted from production pages, with figures counted from public files.",
                         "/transparency/", body, extra_head=f'<link rel="stylesheet" href="{css_href}"><link rel="alternate" type="application/atom+xml" title="BotShelf Vampire: recent material public changes" href="/transparency/changes.atom"><script src="{js_href}" defer></script>')
    foot = ('<footer class="site-footer"><div class="container"><p data-lang="en">If this page and a linked production page or the current checkout ever disagree, the production page and the checkout win. Report a mismatch to support@botshelfvampire.com.</p>'
            '<p data-lang="ja">このページとリンク先の本番ページ・現在のチェックアウトが食い違う場合は、本番ページとチェックアウトが優先です。食い違いは support@botshelfvampire.com へお知らせください。</p></div></footer>')
    h = re.sub(r'<footer class="site-footer">.*?</footer>', foot, h, count=1, flags=re.S)
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "BotShelf Vampire", "item": ORIGIN + "/"},
        {"@type": "ListItem", "position": 2, "name": "Transparency Center", "item": ORIGIN + "/transparency/"}]}
    return h.replace("</head>", f'<script type="application/ld+json">{json.dumps(crumbs, separators=(",", ":"))}</script></head>', 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); a = ap.parse_args()
    site = Path(a.site); blt.assets(site)
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    F = figures(site)
    if len(F["targets"]) < 22 or F["build_total"] == 0:
        sys.exit(f"transparency: could not read figures {F}")
    d = site / "transparency"; d.mkdir(exist_ok=True)
    for old in d.glob("transparency.*"):
        old.unlink()
    js_n = f"transparency.{h8(JS)}.js"; (d / js_n).write_text(JS)
    rq_css = [p.name for p in (site / "requests").glob("request-market.*.css")]
    (d / "index.html").write_text(page(site, F, f"/requests/{rq_css[0]}", f"/transparency/{js_n}", today))
    cj, ca = change_feeds(today); (d / "changes.json").write_text(cj); (d / "changes.atom").write_text(ca)
    smp = site / "sitemap.xml"; s = smp.read_text(); u = ORIGIN + "/transparency/"
    if f"<loc>{u}</loc>" not in s:
        smp.write_text(s.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n</urlset>"))
    print(json.dumps({"transparency_page": "/transparency/", "figures": {k: v for k, v in F.items() if k != "targets"}, "targets": len(F["targets"])}))


if __name__ == "__main__":
    main()
