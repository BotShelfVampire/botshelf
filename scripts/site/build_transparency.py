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
    ("2026-10-05", "The LangGraph, CrewAI and OpenAI Agents SDK team runners can now write an evidence record (--eval-record, BSV eval record schema 1.0) that passes scripts/validate-eval-run.mjs. A run counts as passed only when every required section is present and you typed yes; a missing section or no is recorded as failed. Facts, numbers and quotes are not checked by it, input and draft are stored as sha256 only, and no reviewer is filled in for you. n8n has no record (its result is the n8n execution view). Checked in the team-runner smoke test on the real libraries against a local stub server; not a real model run, UNTESTED_RUNTIME.", "/library/toolkit/langgraph-team-runner/"),
    ("2026-10-04", "Symbol scans on MQL4 (iRSI / iClose on each listed symbol or every Market Watch symbol, once per closed chart bar; a symbol without enough history yet is skipped and counted), now 8 targets. On MQL4 pivots and divergence are generated only inside the scan recipe, so other recipes are unchanged. MQL4 now has its own BSV check (MQL4-subset translator and MT4 API model, all 14 recipes; the scan run with per-symbol bars, a late-starting symbol, Market Watch and an unknown symbol; mutants caught). Not MetaTrader 4, UNTESTED_RUNTIME.", "/trading/build/coverage/"),
    ("2026-10-04", "All 4 AI team runners now have a repeatable smoke test (scripts/site/smoke_team_runners.py): LangGraph, CrewAI, the OpenAI Agents SDK and n8n run unchanged on the real libraries or the real n8n CLI against a local stub server with scripted replies. It checks the requests sent, the missing-section rewrite, the approval step, what is saved, and that no outside call shows up at a local proxy recorder (the OpenAI Agents SDK runner keeps tracing off). No model, no paid API. This checks the wiring only, not answer quality on a real model; the runners stay UNTESTED_RUNTIME.", "/library/toolkit/openai-agents-team-runner/"),
    ("2026-10-04", "Symbol scans on NinjaTrader 8 (AddDataSeries per symbol, each symbol checked when its own bar closes) and cTrader (MarketData.GetBars per symbol, once per new chart bar), now 7 targets. On these two, pivots and divergence are generated only inside the scan recipe, so other recipes are unchanged. All 14 NinjaTrader outputs compile against a BSV stand-in, and both scan outputs were run on BSV synthetic bars against the Python reference with 8 mutants caught; not NinjaTrader or cTrader, UNTESTED_RUNTIME. MQL4 and AmiBroker still print run one chart per symbol.", "/trading/build/coverage/"),
    ("2026-10-04", "AI Team Regression Checklist (owner-written, framework-neutral: golden tasks, tool routing, handoff integrity, negative tests, evidence check, regression rule, SHIP / FIX / HOLD) listed in the AI toolkit as SOURCE_PREPARED under a new job, Regression check before shipping. The checklist text is unchanged; the source is behind the free email gate like other toolkit sources.", "/library/toolkit/ai-team-regression/"),
    ("2026-10-04", "Symbol scans (scanner.symbol_set) generated on 5 targets: Pine v6 (request.security per symbol at its closed bar, up to 40 symbols), MQL5 (SymbolSelect and a loop over the list or Market Watch once per closed chart bar) and backtrader, Backtesting.py and NautilusTrader (a dict of symbol data, --scan on the command line). The other 17 targets now say unsupported for this target: run one chart per symbol instead of a bare TODO; NinjaTrader, cTrader, MQL4 and AmiBroker have their own multi-symbol APIs that BSV does not generate yet. Checked in the BSV models and the 3 Python libraries; not TradingView or MetaTrader 5, UNTESTED_RUNTIME.", "/trading/build/coverage/"),
    ("2026-10-04", "Value panels (Comment() at the bar that just closed) and webhook JSON rendered on MQL5, checked in the BSV MQL5 model on every incremental call. MT5 indicators cannot call WebRequest (MQL5 reference: only Expert Advisors and scripts), so the MQL5 starter prints the webhook JSON once per closed bar; send it from your own EA. Not MetaTrader 5, UNTESTED_RUNTIME. Only scanner.symbol_set remains TODO on MQL5.", "/trading/build/coverage/"),
    ("2026-10-04", "Pivots, liquidity-sweep candidates, regular divergence and zones rendered on MQL5 (stateless scan back from each bar, no lookahead; zones as two line buffers), checked in the BSV MQL5 model against an independent chronological reference on every calculated bar, with mutants caught; not MetaTrader 5, UNTESTED_RUNTIME. MQL5 TODO lines across the 14 recipes: from 12 to 6.", "/trading/build/coverage/"),
    ("2026-10-04", "Recipe trend-pullback-composite, follow-up: the pullback level is now 40 (its own Builder parameter) while the trigger stays at 45, so the condition means a real dip, then recovery. With both at 45 the pullback condition was redundant. The alert condition still holds on the test bars of every BSV check (fewer times than before). Changelog on the recipe page.", "/trading/tools/bsv-recipe-trend-pullback-composite.html#changelog"),
    ("2026-10-04", "Recipe trend-pullback-composite (BSV original), functional fix: the old condition needed the EMA 21 / 89 cross-up event and RSI at or below 45 on the same bar, which never held on BSV test data. It now uses trend state EMA 21 above EMA 89, a pullback (RSI at or below 45 on one of the last 5 bars, editable) and a trigger (RSI crosses back above 45 on a closed bar). Same change on all 22 starters, generated by the new signal.recent block and signal.threshold with a right-hand value; download the starters again. Changelog on the recipe page.", "/trading/tools/bsv-recipe-trend-pullback-composite.html#changelog"),
    ("2026-10-04", "MQL5 output now checked by a BSV MQL5-subset translator run against a model of the documented MT5 indicator API (undeclared-name audit, bounds-checked arrays, incremental OnCalculate calls with ticks, alerts once per closed bar, mutants caught; not MetaTrader 5, UNTESTED_RUNTIME). MT5 built-in ATR is a simple average of the true range (ATR.mq5), not Wilder smoothing, so ATR thresholds can differ from other platforms. Ranges and breakouts rendered on MQL5; MQL5 TODO lines across the 14 recipes: from 15 to 12.", "/trading/build/coverage/"),
    ("2026-10-04", "Value panels (table.new on the last bar, [1] = the bar that just closed) and webhooks (alert() with the recipe JSON once per bar close) rendered on Pine v6, checked in BSV's Pine-subset evaluator: every panel cell against the checked series on full and prefix runs, every webhook message parsed as JSON against the payload filled from the bar, mutants caught (not TradingView; UNTESTED_RUNTIME). Pine TODO lines across the 14 recipes: from 6 to 1 (symbol set, TODO on every target).", "/trading/build/coverage/"),
    ("2026-10-04", "Ranges, breakouts, pivots, zones, liquidity-sweep candidates and regular divergence rendered on Pine v6 (ta.valuewhen, ta.highest / ta.lowest, ta.barssince), checked bar by bar against independent references in BSV's Pine-subset evaluator with no-lookahead prefix runs and mutants caught (not TradingView; UNTESTED_RUNTIME). Pine TODO lines across the 14 recipes: from 15 to 6.", "/trading/build/coverage/"),
    ("2026-10-04", "Pine v6 generator output is now checked by a BSV Pine-subset evaluator (indicators, crosses, sessions, higher-timeframe closed bars, alerts, no-lookahead prefix runs, mutants; not TradingView). It found that three recipes referenced an undeclared name in Pine (alerts on blocks Pine does not render yet), which would not compile; TODO blocks are now declared as never-true / empty stubs.", "/trading/build/coverage/"),
    ("2026-10-04", "Ranges, breakouts, pivots, zones, liquidity-sweep candidates and regular divergence rendered on thinkorswim (thinkScript CompoundValue with a one-bar-back self reference, Highest / Lowest), checked bar by bar on 15-minute bars against independent references in BSV's thinkScript-subset evaluator, with no-lookahead prefix runs and mutants caught (not thinkorswim; UNTESTED_RUNTIME).", "/trading/build/coverage/"),
    ("2026-10-04", "Pivots, zones, liquidity-sweep candidates and regular divergence rendered on AmiBroker (HHV / LLV / ValueWhen from the AFL guide), checked bar by bar on 15-minute bars against an independent reference in BSV's AFL-subset evaluator, with no-lookahead prefix runs and 3 mutants caught (not AmiBroker; UNTESTED_RUNTIME).", "/trading/build/coverage/"),
    ("2026-10-04", "Ranges and breakouts (structure.range, signal.breakout) rendered on AmiBroker with the AFL guide's HighestSince / LowestSince / ValueWhen, checked bar by bar on 15-minute bars against an independent window reference in BSV's AFL-subset evaluator (not AmiBroker; UNTESTED_RUNTIME); its range and breakout value panels now show too. coverage.json lists, per target, which recipe block types are rendered and which are TODO.", "/trading/build/coverage/"),
    ("2026-10-04", "AI toolkit hub: Clear filters, and the ask-for-a-framework link carries the framework you filtered by. Robot Pilot's practice-log summary states the dates of the saved sessions (self-reported).", "/library/toolkit/"),
    ("2026-10-04", "Value panels (visual.table) on Tradovate: the API has no panel call, so the field values of each closed bar are kept in per-bar state (not drawn), checked bar by bar in BSV's stub of the documented API (not run on Tradovate; UNTESTED_RUNTIME). Correction: the compatibility notes said only one recipe's panel could be shown; with ranges, breakouts and closed-bar higher timeframes, the Python targets and Tradovate show all 4.", "/trading/build/"),
    ("2026-10-04", "Each AI toolkit page links to the hub filtered by its framework; toolkit.v1.json lists the filter values; the generator coverage page has an Ask link per target that pre-fills the platform on the request form (known platforms only); Robot Pilot log downloads carry the date in the file name.", "/library/toolkit/"),
    ("2026-10-04", "Webhooks (alert.webhook) rendered on Tradovate: dots on the closed bar and the JSON payload built per bar, never sent; checked bar by bar against a separately written fill in BSV's stub of the documented API (not run on Tradovate; UNTESTED_RUNTIME).", "/trading/build/"),
    ("2026-10-04", "AI toolkit hub filters can be shared as links (framework, job, status, search in the URL); the framework list and the Request Market supply table link to those filtered views, and llms.txt describes them. Robot Pilot asks before Clear deletes the sessions saved in this browser.", "/library/toolkit/#tk-matrix"),
    ("2026-10-04", "AI toolkit: the hub lists which jobs each framework has items for, each summary page carries CreativeWork structured data (title, URL, MIT; no ratings), and the Request Market shows AI toolkit items by framework counted from the catalog (not demand). Robot Pilot states the 20-session browser cap next to Save.", "/library/toolkit/#tk-matrix"),
    ("2026-10-04", "Ranges and breakouts (structure.range, signal.breakout) and range-sourced zones rendered on Tradovate, checked bar by bar against an independent reference in BSV's stub of the documented API (not run on Tradovate; UNTESTED_RUNTIME).", "/trading/build/"),
    ("2026-10-04", "AI toolkit pages list related items (same job on other frameworks, more for the same framework); the hub links to asking for a framework or tool not listed; /library/toolkit/toolkit.v1.json states license, source access and runtimeTestedByBSV false per entry. The Robot Pilot CSV adds the pass criteria ticked / recorded per session.", "/library/toolkit/"),
    ("2026-10-04", "Higher timeframe on Tradovate: indicators marked with a higher timeframe are computed from closed higher-timeframe bars only, checked against an independent reference on every bar in BSV's stub of the documented API (not run on Tradovate; UNTESTED_RUNTIME). Coverage: 4 targets with checked closed-bar values.", "/trading/build/coverage/"),
    ("2026-10-04", "llms.txt lists the AI toolkit: the hub, its JSON index and one line per public summary page with framework and catalog status (none runtime-tested by BSV; gated source not listed).", "/llms.txt"),
    ("2026-10-04", "Request form: AI frameworks with BSV toolkit items can be added with one tap, like trading platforms. Robot Pilot: saving a session now says when the 20-session browser log removes the oldest, instead of dropping them silently.", "/requests/#rq-form"),
    ("2026-10-04", "AI toolkits: the Handoff Packet checker can start a blank packet for any AI toolkit item, filling only what the catalog states (job id, NOT_STARTED, source path, framework, catalog status as a limitation); owner approval and results stay blank. In the browser only.", "/library/toolkit/ai-team-handoff/"),
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
