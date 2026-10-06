#!/usr/bin/env python3
"""Homepage "What BSV gives you" layer (growth tranche, 2026-10-06).

Inserts one value-first block directly under the hero image of /index.html.
Every number is counted at build time from files that ship in the same site
tree (no invented metrics). Brand lock: the hero image, logo, fonts, accent
(#bad4b7), the existing catch lines and the Trader / AI hubs are untouched;
the hubs simply follow this block. Copy lives only inside the new block.

Funnel markers use the site's existing data-evt attribute convention. The
site has no analytics script or vendor; nothing new is loaded or sent.

Idempotent: the block lives between BEGIN/END markers and is replaced.
Usage: build_home_value.py --site SITE [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

BEGIN, END = "<!-- bsv-home-value:begin -->", "<!-- bsv-home-value:end -->"
CSS_BEGIN, CSS_END = "<!-- bsv-home-value-css:begin -->", "<!-- bsv-home-value-css:end -->"
HERO_RE = re.compile(r'(<div class="hero">\s*<picture>.*?</picture>\s*</div>\n?)', re.S)

WORKFLOW_TYPES = ("Code workflow", "Dify workflow", "Flowise flow", "Workflow", "Team orchestration")
TEMPLATE_TYPES = ("Skill", "Prompt pack", "Prompt", "Gemini prompt", "DeepSeek prompt", "Cursor instruction", "Claude Code instruction")
RUNTIME_NAMES = {"kimi-code": "Kimi Code", "dify": "Dify", "flowise": "Flowise", "n8n": "n8n", "agentswarm": "AgentSwarm"}

CSS = """/* Homepage value layer: reuses .bsv-hub / .bsv-hub-card / .bsv-hub-ai-paths; layout only. */
.bsv-home-value{padding-top:30px;padding-bottom:30px}
.bsv-home-value h2{margin-bottom:10px}
.bsv-home-value .bsv-hub-lead{margin-bottom:16px}
.bsv-home-value .bsv-hub-grid{margin-top:4px}
.bsv-home-value .bsv-hub-card{min-height:0;padding:15px 17px}
.bsv-home-value .bsv-hub-card h4{font-size:16px;margin:8px 0 6px}
.bsv-home-value .bsv-hub-card p{margin-bottom:10px}
.bsv-home-value .bsv-hub-card-footer{margin-top:auto}
.bsv-home-value .bsv-hub-ai-paths{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:12px 0 10px}
.bsv-home-value .bsv-hub-ai-paths a{padding:12px 15px}
.bsv-home-value .bsv-hub-ai-paths strong span{font-size:inherit;color:inherit}
.bsv-home-value h3{font-size:13px;letter-spacing:.06em;margin:18px 0 0;color:#b4bdca}
.bsv-home-value .ai-targets{margin:8px 0 0}
.bsv-home-value-note{font-size:12px;color:#919dab;margin:10px 0 0}
@media(max-width:950px){.bsv-home-value .bsv-hub-ai-paths{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.bsv-home-value{padding:22px 16px 22px}.bsv-home-value h2{font-size:26px}.bsv-home-value .bsv-hub-lead{font-size:14px;line-height:1.55}.bsv-home-value .bsv-hub-ai-paths{grid-template-columns:1fr;gap:8px}.bsv-home-value .bsv-hub-ai-paths a{padding:10px 13px}.bsv-home-value .bsv-hub-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.bsv-home-value .bsv-hub-card{padding:11px 12px}.bsv-home-value .bsv-hub-card h4{font-size:14px;margin:6px 0 0}.bsv-home-value .bsv-hub-card p,.bsv-home-value .bsv-hub-card-platform,.bsv-home-value .bsv-hub-card-footer,.bsv-home-value .bsv-hub-price{display:none}}
"""


def J(site: Path, rel: str):
    return json.loads((site / rel).read_text())


def counts(site: Path) -> dict:
    cat = J(site, "trading/catalog.json")
    caps = J(site, "capabilities/index.json")["capabilities"]
    recipes = [c for c in caps if str(c.get("capabilityId", "")).startswith("bsv.recipe.")]
    rec_platforms = set()
    for c in recipes:
        rec_platforms.update((c.get("runtime") or {}).get("requirements") or [])
    si = J(site, "library/search-index.json")
    tk = J(site, "library/toolkit/toolkit.v1.json")
    reg = J(site, "library/registry.json")
    plat = J(site, "trading/platforms.json")
    guides = sorted(p.parent.name for p in (site / "trading/guides").glob("*/index.html"))
    wf = [e for e in si if e.get("type") in WORKFLOW_TYPES]
    wf_rt = sorted({e["runtime"] for e in wf}, key=lambda r: (-sum(1 for e in wf if e["runtime"] == r), r))
    tpl = [e for e in si if e.get("type") in TEMPLATE_TYPES]
    return {
        "trading_tools": len(cat),
        "trading_platforms": sorted({p for e in cat for p in e.get("platforms", [])}),
        "recipes": len(recipes),
        "recipe_platforms": len(rec_platforms),
        "library_total": len(si),
        "library_runtimes": len({e.get("runtime") for e in si}),
        "library_all_free": all(e.get("access") == "free" for e in si),
        "workflows": len(wf),
        "workflow_runtimes": [RUNTIME_NAMES.get(r, r) for r in wf_rt],
        "skills": sum(1 for e in si if e.get("type") == "Skill"),
        "templates": len(tpl),
        "toolkits": tk["counts"]["entries"],
        "toolkit_frameworks": tk["counts"]["frameworks"],
        "toolkit_framework_names": [f for f, _ in sorted(__import__("collections").Counter(e.get("framework") for e in tk["entries"] if e.get("framework") and e.get("framework") != "Any framework").items(), key=lambda kv: (-kv[1], kv[0]))],
        "teams": reg["counts"]["teams"],
        "team_impls": reg["counts"]["implementations"],
        "platforms_compared": plat["total"],
        "guides": len(guides),
        "robot_curricula": len(list((site / "robot-pilot/curricula").glob("*.json"))),
        "robot_recipes": len(list((site / "robot-pilot/teleop-recipes").glob("*.json"))),
    }


def b(ja: str, en: str) -> str:
    return f"<span data-bsv-ja>{ja}</span><span data-bsv-en>{en}</span>"


def card(key, kind, title, desc, platform, href, evt, href_ja=None):
    def link(inner):
        if href_ja:
            return (f'<a href="{href}" data-bsv-en data-evt="{evt}">{inner[1]}</a>'
                    f'<a href="{href_ja}" data-bsv-ja data-evt="{evt}">{inner[0]}</a>')
        return f'<a href="{href}" data-evt="{evt}">{b(*inner)}</a>'
    return (f'<article class="bsv-hub-card" data-bsv-value-card="{key}"><div class="bsv-hub-card-top">'
            f'<span class="bsv-hub-kind">{b(*kind)}</span><span class="bsv-hub-price">{b("無料", "Free")}</span></div>'
            f'<h4>{link(title)}</h4><p>{b(*desc)}</p><div class="bsv-hub-card-platform">{html.escape(platform)}</div>'
            f'<div class="bsv-hub-card-footer"><span></span>{link(("開く →", "Open →"))}</div></article>')


def goal(key, title, sub, href, href_ja=None):
    evt = f"home_goal_{key}"
    if href_ja:
        return (f'<a href="{href}" data-bsv-en data-evt="{evt}"><strong>{title[1]}</strong><span>{sub[1]}</span></a>'
                f'<a href="{href_ja}" data-bsv-ja data-evt="{evt}"><strong>{title[0]}</strong><span>{sub[0]}</span></a>')
    return f'<a href="{href}" data-evt="{evt}"><strong>{b(*title)}</strong><span>{b(*sub)}</span></a>'


def block(c: dict) -> str:
    tp = " · ".join(c["trading_platforms"])
    wr = ", ".join(c["workflow_runtimes"])
    cards = [
        card("tools", ("ツールとコード", "Tools & code"),
             (f"ソースを読めるチャートツール {c['trading_tools']}件", f"{c['trading_tools']} chart tools with source"),
             (f"EA・インジケーター・ストラテジー・取引管理。さらに{c['recipes']}のレシピから、最大{c['recipe_platforms']}プラットフォーム向けのスターターコードを作れます。",
              f"EAs, indicators, strategies and trade managers, plus {c['recipes']} recipes that generate starter code for up to {c['recipe_platforms']} platforms."),
             tp, "/trading/tools/", "home_primitive_tools"),
        card("workflows", ("ワークフロー", "Workflows"),
             (f"AIワークフロー {c['workflows']}件", f"{c['workflows']} AI workflows"),
             ("調査、コードレビュー、資料作成などの仕事を、手順ごと組み込めます。", "Research, code review, drafting and more, laid out step by step so you can adapt them."),
             wr, "/library/", "home_primitive_workflows"),
        card("agents", ("AIエージェント", "AI agents"),
             (f"エージェントのテンプレート {c['toolkits']}件・{c['toolkit_frameworks']}フレームワーク", f"{c['toolkits']} agent toolkits across {c['toolkit_frameworks']} frameworks"),
             (f"仕事別に整理しています。AIチーム{c['teams']}種（{c['team_impls']}の実装）もあります。", f"Organised by job, alongside {c['teams']} AI teams in {c['team_impls']} runtime implementations."),
             " · ".join(c["toolkit_framework_names"][:6]), "/library/toolkit/", "home_primitive_agents"),
        card("templates", ("テンプレート", "Templates & prompts"),
             (f"スキル・プロンプト・指示書 {c['templates']}件", f"{c['templates']} skills, prompts and instructions"),
             (f"スキル{c['skills']}件のほか、Cursor・Claude Code・Gemini・DeepSeek向けの指示書やプロンプト。", f"{c['skills']} skills plus prompts and instruction files for Cursor, Claude Code, Gemini, DeepSeek and more."),
             f"{c['library_runtimes']} runtimes · Build Library", "/library/skills/", "home_primitive_templates"),
        card("research", ("調査と比較", "Research & comparisons"),
             (f"{c['platforms_compared']}サービスの比較と調査ガイド{c['guides']}本", f"{c['platforms_compared']} platforms compared, {c['guides']} research guides"),
             ("チャートの代替、Pine Scriptの移行、リペイントやバックテストの確認を、公式情報から。", "Charting alternatives, Pine Script migration, repainting and backtest checks, from official sources."),
             "TradingView alternatives · Pine · order flow", "/trading/guides/tradingview-alternatives/", "home_primitive_research",
             href_ja="/trading/ja/guides/tradingview-alternatives/"),
        card("robotics", ("ロボティクス", "Robotics"),
             ("ロボット遠隔操作の練習、シミュレーションから", "Robot teleoperation practice, simulation first"),
             ("SO-101の教材で練習し、各セッションを記録に残して見直します。実機の操作許可ではありません。", "Practise with an SO-101 curriculum and keep a structured record of each session. Not permission to run real hardware."),
             f"Robot Pilot Academy · {c['robot_curricula']} curriculum · {c['robot_recipes']} teleop recipe", "/robot-pilot/", "home_primitive_robotics"),
    ]
    goals = [
        goal("ai_workflow", ("AIワークフローを組む", "Build an AI workflow"), ("n8n・Dify・Flowiseなどで使える手順", "Steps for n8n, Dify, Flowise and more"), "/library/workflows/"),
        goal("find_trading_tool", ("トレード用ツールを探す", "Find a trading tool"), ("用途・プラットフォームで絞り込み", "Filter by job and platform"), "/trading/tools/"),
        goal("build_trading_tool", ("自分のツールを作る", "Build your own trading tool"), ("ブラウザでレシピからコードを生成", "Generate code from a recipe in your browser"), "/trading/tools/bsv-builder.html"),
        goal("robot_practice", ("ロボット操作を練習する", "Practise robot teleoperation"), ("実機の前に、シミュレーションで", "In simulation, before real hardware"), "/robot-pilot/"),
        goal("compare", ("技術や道具を比べる", "Compare platforms and approaches"), ("選ぶ前に、公式情報で比較", "Check official sources before you choose"), "/trading/guides/tradingview-alternatives/", "/trading/ja/guides/tradingview-alternatives/"),
        goal("agent_sdks", ("エージェントのSDKを探す", "Find agent SDKs and frameworks"), ("フレームワーク別のテンプレート", "Templates grouped by framework"), "/library/toolkit/"),
    ]
    fields = [("ai", "/library/", ("AI", "AI")), ("trading", "/trading/", ("トレード", "Trading")), ("robotics", "/robot-pilot/", ("ロボティクス", "Robotics"))]
    chips = "".join(f'<a class="ai-chip" href="{h}" data-evt="home_field_{k}">{b(*t)}</a>' for k, h, t in fields)
    free = ("ここに挙げたものは、すべて無料で使えます。ソースやダウンロードにはメール確認が必要です。", "Everything listed here is free to use. Source and downloads need a verified email.") if c["library_all_free"] else ("", "")
    return (
        f'{BEGIN}\n<section class="bsv-hub bsv-home-value" id="what-bsv-gives" data-bsv-home-value aria-labelledby="bsv-value-title" data-evt="home_value">'
        f'<div class="bsv-hub-topline"><span class="bsv-hub-eyebrow">WHAT BSV GIVES YOU</span>'
        f'<a href="/search/" class="bsv-hub-crosslink" data-evt="home_value_search">{b("サイト全体を検索 →", "Search the whole site →")}</a></div>'
        f'<h2 id="bsv-value-title">{b("ここで使えるもの。", "What you can use here.")}</h2>'
        f'<p class="bsv-hub-lead">{b("トレードのツールとコード、AIのワークフローとエージェント、ロボット操作の練習。" + free[0], "Trading tools and code, AI workflows and agents, and robot teleoperation practice. " + free[1])}</p>'
        f'<div class="bsv-hub-grid" data-bsv-value-grid>{"".join(cards)}</div>'
        f'<h3 id="bsv-goal-title">{b("目的から始める", "Start with a goal")}</h3>'
        f'<nav class="bsv-hub-ai-paths" aria-labelledby="bsv-goal-title" data-bsv-goals>{"".join(goals)}</nav>'
        f'<nav class="ai-targets" aria-label="Fields" data-bsv-fields>{chips}</nav>'
        f'<p class="bsv-home-value-note">{b("何を確認済みで、何が未確認かは、各ページに表示しています。", "Each page shows what has and hasn&#39;t been checked.")}</p>'
        f'</section>\n{END}\n'
    )


EVT_ADD = [  # existing elements that start the funnel: add data-evt only (no copy change)
    (re.compile(r'<a class="btn-fat btn-solid" href="#packs" data-i18n="ctaBrowse"(?! data-evt)'), '<a class="btn-fat btn-solid" href="#packs" data-i18n="ctaBrowse" data-evt="home_hero_cta_browse"'),
    (re.compile(r'<a href="#trader-library" data-bsv-area="trading"(?! data-evt)'), '<a href="#trader-library" data-bsv-area="trading" data-evt="home_audience_trading"'),
    (re.compile(r'<a href="#ai-library" data-bsv-area="ai"(?! data-evt)'), '<a href="#ai-library" data-bsv-area="ai" data-evt="home_audience_ai"'),
    (re.compile(r'<a class="header-register header-register-inline" href="/register.html" data-i18n="navRegister"(?! data-evt)'), '<a class="header-register header-register-inline" href="/register.html" data-i18n="navRegister" data-evt="home_register_header"'),
]


def apply(site: Path) -> dict:
    p = site / "index.html"
    t = p.read_text()
    c = counts(site)
    css_name = f"home-value.{hashlib.sha256(CSS.encode()).hexdigest()[:8]}.css"
    css_dir = site / "css"
    for old in css_dir.glob("home-value.*.css"):
        if old.name != css_name:
            old.unlink()
    (css_dir / css_name).write_text(CSS)
    t = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", t, flags=re.S)
    t = re.sub(re.escape(CSS_BEGIN) + r".*?" + re.escape(CSS_END), "", t, flags=re.S)
    if not HERO_RE.search(t):
        raise SystemExit("hero block not found in index.html")
    t = HERO_RE.sub(lambda m: m.group(1) + block(c), t, count=1)
    t = t.replace("</head>", f'{CSS_BEGIN}<link rel="stylesheet" href="/css/{css_name}">{CSS_END}</head>', 1)
    for rx, rep in EVT_ADD:
        evt = re.search(r'data-evt="([^"]+)"', rep).group(1)
        if f'data-evt="{evt}"' not in t:
            t = rx.sub(rep, t, count=1)
    p.write_text(t)
    return {"css": css_name, **{k: v for k, v in c.items() if isinstance(v, int)}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true", help="print counts only")
    a = ap.parse_args()
    site = Path(a.site)
    if a.check:
        print(json.dumps(counts(site), ensure_ascii=False))
        return 0
    print(json.dumps(apply(site), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
