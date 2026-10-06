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
import urllib.parse
from pathlib import Path

BEGIN, END = "<!-- bsv-home-value:begin -->", "<!-- bsv-home-value:end -->"
CSS_BEGIN, CSS_END = "<!-- bsv-home-value-css:begin -->", "<!-- bsv-home-value-css:end -->"
BAND_BEGIN, BAND_END = "<!-- bsv-home-band:begin -->", "<!-- bsv-home-band:end -->"
# Owner-approved hero headline band (2026-10-06 21:33 JST; interim sub-line = fields with live content only).
# Text goes through the existing i18n (data-i18n + window.PAGE_I18N) so en/ja/es/zh/ko each show their own language.
BAND_I18N = {
    "en": {"heroBandH": "Tools, workflows and AI agents for people building what's next.",
           "heroBandSub": "Find, compare and use practical resources for AI, trading and robotics.",
           "heroBandCtaExplore": "Explore what you can do", "heroBandCtaBrowseAll": "Browse all resources"},
    "ja": {"heroBandH": "次に作るための、ツール・ワークフロー・AIエージェント。",
           "heroBandSub": "AI、トレード、ロボティクスの実用リソースを、探す・比べる・使う。",
           "heroBandCtaExplore": "できることを見る", "heroBandCtaBrowseAll": "すべてのリソースを見る"},
    "es": {"heroBandH": "Herramientas, flujos de trabajo y agentes de IA para quienes construyen lo que viene.",
           "heroBandSub": "Encuentra, compara y usa recursos prácticos de IA, trading y robótica.",
           "heroBandCtaExplore": "Explora lo que puedes hacer", "heroBandCtaBrowseAll": "Ver todos los recursos"},
    "zh": {"heroBandH": "为构建未来的人准备的工具、工作流和 AI 智能体。",
           "heroBandSub": "查找、比较并使用 AI、交易和机器人领域的实用资源。",
           "heroBandCtaExplore": "看看你能做什么", "heroBandCtaBrowseAll": "浏览全部资源"},
    "ko": {"heroBandH": "다음을 만드는 사람들을 위한 도구, 워크플로, AI 에이전트.",
           "heroBandSub": "AI, 트레이딩, 로보틱스의 실용 리소스를 찾고, 비교하고, 사용하세요.",
           "heroBandCtaExplore": "할 수 있는 일 보기", "heroBandCtaBrowseAll": "모든 리소스 보기"},
}
PAGE_I18N_RE = re.compile(r"(window\.PAGE_I18N = )(\{.*?\n\})(;\s*</script>)", re.S)
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
.bsv-home-band{padding-top:26px;padding-bottom:6px}
.bsv-home-band h2{margin:0 0 10px;max-width:22em}
.bsv-home-band .bsv-hub-lead{margin:0 0 16px;max-width:46em}
.bsv-home-band-ctas{display:flex;flex-wrap:wrap;gap:10px}
.bsv-home-value-note{font-size:12px;color:#919dab;margin:10px 0 0}
.bsv-home-cats{padding-top:22px;padding-bottom:8px}
.bsv-home-cats h2,.bsv-home-goals h2,.bsv-home-value h2{font-size:22px;line-height:1.3;letter-spacing:-.02em;margin:0 0 12px}
.bsv-home-cat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.bsv-home-cat{display:flex;flex-direction:column;gap:3px;border:1px solid #3b4757;border-radius:7px;padding:12px 14px;background:#141b25;min-height:70px}
.bsv-home-cat:hover{border-color:#bad4b7}
.bsv-home-cat strong{font-size:15px;line-height:1.3}
.bsv-home-cat-status{font-size:12px;color:#b0ceac}
.bsv-home-cat-soon{background:none;border-style:dashed}
.bsv-home-cat-soon .bsv-home-cat-status,.bsv-home-cat-note{font-size:11px;color:#919dab}
.bsv-home-goals{padding-top:18px;padding-bottom:8px}
.bsv-home-goals .bsv-hub-nav{padding:0;margin:0 0 10px;max-width:none;border:1px solid #2b313a;border-radius:6px}
.bsv-home-goals .bsv-hub-nav a{min-height:58px}
.bsv-home-goals .bsv-hub-ai-paths{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0}
.bsv-home-goals .bsv-hub-ai-paths a{padding:12px 15px}
.bsv-home-goals .bsv-hub-ai-paths strong span{font-size:inherit;color:inherit}
.bsv-home-goals .bsv-home-goal-soon{border-style:dashed;background:none}
@media(max-width:950px){.bsv-home-value .bsv-hub-ai-paths,.bsv-home-goals .bsv-hub-ai-paths{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.bsv-home-cats{padding:14px 16px 4px}.bsv-home-goals{padding:14px 16px 4px}.bsv-home-cats h2,.bsv-home-goals h2,.bsv-home-value h2{font-size:20px;margin-bottom:10px}.bsv-home-cat-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.bsv-home-cat{padding:10px 12px;min-height:58px}.bsv-home-cat strong{font-size:14px}.bsv-home-goals .bsv-hub-ai-paths{grid-template-columns:1fr;gap:8px}.bsv-home-goals .bsv-hub-ai-paths a{padding:10px 13px}.bsv-home-band{padding:18px 16px 2px}.bsv-home-band h2{font-size:24px;line-height:1.25}.bsv-home-band .bsv-hub-lead{font-size:14px;line-height:1.5;margin-bottom:12px}.bsv-home-band .bsv-hub-button{padding:10px 14px;min-height:40px}.bsv-home-value{padding:22px 16px 22px}.bsv-home-value .bsv-hub-lead{font-size:14px;line-height:1.55}.bsv-home-value .bsv-hub-ai-paths{grid-template-columns:1fr;gap:8px}.bsv-home-value .bsv-hub-ai-paths a{padding:10px 13px}.bsv-home-value .bsv-hub-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.bsv-home-value .bsv-hub-card{padding:11px 12px}.bsv-home-value .bsv-hub-card h4{font-size:14px;margin:6px 0 0}.bsv-home-value .bsv-hub-card p,.bsv-home-value .bsv-hub-card-platform,.bsv-home-value .bsv-hub-card-footer,.bsv-home-value .bsv-hub-price{display:none}}
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
        **category_counts(site, si),
    }


def category_counts(site: Path, si: list) -> dict:
    """Per-category live counts. Sources: the shipped site-search index (rows per scope), the Build Library
    search index (use case Data) and the Robot Pilot curricula / teleop recipes. 0 = no live content (Coming soon)."""
    idx = sorted((site / "search").glob("index.v*.json"))
    ref = (site / "search/index.html").read_text() if (site / "search/index.html").exists() else ""
    js = sorted((site / "js").glob("bsv-search-page.v*.js"))
    used = None
    for j in reversed(js):
        if f"/js/{j.name}" in ref:
            m = re.search(r"/search/(index\.v[\w]+\.json)", j.read_text())
            used = site / "search" / m.group(1) if m else None
            break
    sidx = json.loads((used or idx[-1]).read_text())
    rows, sc = sidx["rows"], sidx.get("counts") or {}
    blob = [json.dumps(e, ensure_ascii=False).lower() for e in rows] + [json.dumps(e, ensure_ascii=False).lower() for e in si]
    def kw(*words):
        return sum(1 for b_ in blob if any(re.search(rf"\b{w}", b_) for w in words))
    fc = field_counts(site)
    rp = len(list((site / "robot-pilot/curricula").glob("*.json"))) + len(list((site / "robot-pilot/teleop-recipes").glob("*.json")))
    out = {
        "cat_ai": sc["ai"] + sc["build"] if {"ai", "build"} <= set(sc) else sum(1 for e in rows if e.get("s") in ("ai", "build")),
        "cat_trading": sc.get("trading", sum(1 for e in rows if e.get("s") == "trading")),
        **fc,
    }
    out["cat_robotics"] = rp + int(fc.get("cat_robotics") or 0)
    return out

def field_counts(site: Path) -> dict:
    """Healthcare / Robotics / Data / Space / Biotech / Quantum: BSV recipes + verified sources + Field Lab tools published on /fields/<key>/, read from the
    /fields/index.json that build_fields.py writes in the same build. No file or no page = 0 (Coming soon)."""
    p = site / "fields/index.json"
    cats = json.loads(p.read_text()).get("categories", {}) if p.exists() else {}
    out = {}
    for key in ("healthcare", "robotics", "data", "space", "biotech", "quantum"):
        c = cats.get(key) or {}
        live = (site / "fields" / key / "index.html").exists()
        out[f"cat_{key}"] = int(c.get("recipes", 0)) + int(c.get("sources", 0)) + int(c.get("tools", 0)) if live else 0
    return out


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
        card("robotics", ("練習教材", "Practice courses"),
             ("ロボット遠隔操作の練習、シミュレーションから", "Robot teleoperation practice, simulation first"),
             ("SO-101の教材で練習し、各セッションを記録に残して見直します。実機の操作許可ではありません。", "Practise with an SO-101 curriculum and keep a structured record of each session. Not permission to run real hardware."),
             f"Robot Pilot Academy · {c['robot_curricula']} curriculum · {c['robot_recipes']} teleop recipe", "/robot-pilot/", "home_primitive_robotics"),
    ]
    free_ok = c["library_all_free"]
    return (
        f'{BEGIN}\n<section class="bsv-hub bsv-home-value" id="what-bsv-gives" data-bsv-home-value aria-labelledby="bsv-value-title" data-evt="home_value">'
        f'<div class="bsv-hub-topline"><span class="bsv-hub-eyebrow" data-i18n="homeValueEyebrow">CONTENT TYPES</span>'
        f'<a href="/search/" class="bsv-hub-crosslink" data-evt="home_value_search">{b("サイト全体を検索 →", "Search the whole site →")}</a></div>'
        f'{i("homeValueTitle", STATIC_I18N["homeValueTitle"][0], "h2", " id=\"bsv-value-title\"")}'
        + (f'{i("homeValueLead", STATIC_I18N["homeValueLead"][0], "p", " class=\"bsv-hub-lead\"")}' if free_ok else "")
        + f'<div class="bsv-hub-grid" data-bsv-value-grid>{"".join(cards)}</div>'
        f'<p class="bsv-home-value-note">{b("何を確認済みで、何が未確認かは、各ページに表示しています。", "Each page shows what has and hasn&#39;t been checked.")}</p>'
        f'</section>\n{END}\n'
    )


CATS_BEGIN, CATS_END = "<!-- bsv-home-cats:begin -->", "<!-- bsv-home-cats:end -->"
GOALS_BEGIN, GOALS_END = "<!-- bsv-home-goals:begin -->", "<!-- bsv-home-goals:end -->"
AUDIENCE_NAV_RE = re.compile(r'<nav class="bsv-hub-nav" data-bsv-audience-nav.*?</nav>', re.S)
LANGS = ("en", "ja", "es", "zh", "ko")
# key, href (live content) or None (coming soon -> site search), names en/ja/es/zh/ko
CATS = [
    ("ai", "/library/", ("AI", "AI", "IA", "AI", "AI")),
    ("trading", "/trading/", ("Trading", "トレード", "Trading", "交易", "트레이딩")),
    ("robotics", "/fields/robotics/", ("Robotics", "ロボティクス", "Robótica", "机器人", "로보틱스")),
    ("healthcare", "/fields/healthcare/", ("Healthcare & Medical Robotics", "ヘルスケア・医療ロボティクス", "Salud y robótica médica", "医疗健康与医疗机器人", "헬스케어·의료 로보틱스")),
    ("data", "/fields/data/", ("Data", "データ", "Datos", "数据", "데이터")),
    ("space", "/fields/space/", ("Space", "宇宙", "Espacio", "航天", "우주")),
    ("biotech", "/fields/biotech/", ("Biotech", "バイオ", "Biotecnología", "生物技术", "바이오")),
    ("quantum", "/fields/quantum/", ("Quantum", "量子", "Cuántica", "量子", "양자")),
]
CAT_SEARCH = {"healthcare": "medical robotics", "space": "space", "biotech": "biotech", "quantum": "quantum"}
UNITS = {  # live-count wording per category, {n} = count
    "ai": ("{n} resources", "リソース {n}件", "{n} recursos", "{n} 项资源", "리소스 {n}개"),
    "trading": ("{n} resources", "リソース {n}件", "{n} recursos", "{n} 项资源", "리소스 {n}개"),
    "robotics": ("{n} simulation resources", "シミュレーション教材 {n}件", "{n} recursos de simulación", "{n} 项仿真资源", "시뮬레이션 자료 {n}개"),
    "data": ("{n} data-analysis resources", "データ分析リソース {n}件", "{n} recursos de análisis de datos", "{n} 项数据分析资源", "데이터 분석 리소스 {n}개"),
    "healthcare": ("{n} recipes, tools & sources", "レシピ・ツール・出典 {n}件", "{n} recetas, herramientas y fuentes", "{n} 个配方、工具与来源", "레시피·도구·출처 {n}개"),
    "space": ("{n} recipes, tools & sources", "レシピ・ツール・出典 {n}件", "{n} recetas, herramientas y fuentes", "{n} 个配方、工具与来源", "레시피·도구·출처 {n}개"),
    "biotech": ("{n} recipes, tools & sources", "レシピ・ツール・出典 {n}件", "{n} recetas, herramientas y fuentes", "{n} 个配方、工具与来源", "레시피·도구·출처 {n}개"),
    "quantum": ("{n} recipes, tools & sources", "レシピ・ツール・出典 {n}件", "{n} recetas, herramientas y fuentes", "{n} 个配方、工具与来源", "레시피·도구·출처 {n}개"),
}
SOON = ("Coming soon", "準備中", "Próximamente", "即将推出", "준비 중")
RESEARCH_ONLY = ("Research & simulation only", "研究・シミュレーション用途のみ", "Solo investigación y simulación", "仅限研究与仿真", "연구·시뮬레이션 전용")
STATIC_I18N = {
    "homeCatsTitle": ("Categories", "カテゴリー", "Categorías", "类别", "카테고리"),
    "homeCatsLead": ("Counts are computed from what is published right now. A field with nothing published yet is marked Coming soon.",
                     "数は、いま公開している内容から自動で数えています。まだ何も公開していない分野は「準備中」と表示します。",
                     "Las cifras se calculan a partir de lo publicado ahora mismo. Un campo sin nada publicado aparece como «Próximamente».",
                     "数字根据当前已发布的内容自动统计。尚未发布任何内容的领域标为“即将推出”。",
                     "숫자는 지금 공개된 내용에서 자동으로 집계합니다. 아직 공개된 것이 없는 분야는 '준비 중'으로 표시합니다."),
    "homeGoalsTitle": ("Browse by goal", "目的から探す", "Explorar por objetivo", "按目标浏览", "목표별로 찾기"),
    "homeValueEyebrow": ("CONTENT TYPES", "コンテンツの種類", "TIPOS DE CONTENIDO", "内容类型", "콘텐츠 유형"),
    "homeValueTitle": ("What you can use on BSV", "BSVで使えるもの", "Lo que puedes usar en BSV", "在 BSV 上可以使用的内容", "BSV에서 쓸 수 있는 것"),
    "homeValueLead": ("Content types across the categories above, all free. Guides, comparisons and tool pages are open to everyone. Source and downloads hosted on BSV open after you verify your email; author-hosted links, such as Position Sizer, need no BSV email verification.",
                      "上のカテゴリーをまたぐ、コンテンツの種類です。どれも無料です。ガイド・比較・ツール紹介のページは、どなたでも読めます。BSVで配布しているソースとダウンロードは、メール確認のあとに開きます。Position Sizer のように原作者が配布しているリンクは、BSVのメール確認なしで使えます。",
                      "Tipos de contenido de las categorías anteriores, todos gratuitos. Las guías, comparativas y fichas de herramientas están abiertas a todos. El código fuente y las descargas alojados en BSV se abren tras verificar tu correo; los enlaces alojados por el autor, como Position Sizer, no requieren verificación de correo en BSV.",
                      "以上各类别中的内容类型，全部免费。指南、比较和工具介绍页面对所有人开放。BSV 托管的源码和下载需在验证邮箱后打开；由原作者托管的链接（如 Position Sizer）无需 BSV 邮箱验证。",
                      "위 카테고리 전반의 콘텐츠 유형이며 모두 무료입니다. 가이드, 비교, 도구 소개 페이지는 누구나 볼 수 있습니다. BSV가 호스팅하는 소스와 다운로드는 이메일 인증 후 열리며, Position Sizer처럼 원작자가 호스팅하는 링크는 BSV 이메일 인증이 필요 없습니다."),
    "siteSearchPh": ("Search tools, workflows, AI agents, research…", "ツール・ワークフロー・AIエージェント・調査を検索", "Busca herramientas, flujos, agentes de IA, investigación…", "搜索工具、工作流、AI 智能体、研究…", "도구, 워크플로, AI 에이전트, 리서치 검색…"),
    "siteSearchHint": ("Searches the whole site: tools, workflows, AI agents, research guides and the Build Library", "サイト全体を検索します（ツール、ワークフロー、AIエージェント、調査ガイド、Build Library）",
                       "Busca en todo el sitio: herramientas, flujos, agentes de IA, guías y la Build Library", "搜索全站：工具、工作流、AI 智能体、研究指南和 Build Library",
                       "사이트 전체 검색: 도구, 워크플로, AI 에이전트, 리서치 가이드, Build Library"),
}
# key, href, href_ja (optional), coming_soon, title en/ja/es/zh/ko, sub en/ja/es/zh/ko
GOALS = [
    ("ai_workflow", "/library/workflows/", None, False,
     ("Build an AI workflow", "AIワークフローを組む", "Crear un flujo de trabajo de IA", "搭建 AI 工作流", "AI 워크플로 만들기"),
     ("Steps for n8n, Dify, Flowise and more", "n8n・Dify・Flowiseなどで使える手順", "Pasos para n8n, Dify, Flowise y más", "适用于 n8n、Dify、Flowise 等的步骤", "n8n, Dify, Flowise 등에서 쓰는 단계")),
    ("find_trading_tool", "/trading/tools/", None, False,
     ("Find trading tools", "トレード用ツールを探す", "Buscar herramientas de trading", "查找交易工具", "트레이딩 도구 찾기"),
     ("Filter by job and platform", "用途・プラットフォームで絞り込み", "Filtra por tarea y plataforma", "按用途和平台筛选", "용도와 플랫폼으로 필터")),
    ("build_trading_tool", "/trading/tools/bsv-builder.html", None, False,
     ("Build your own trading tool", "自分のツールを作る", "Crear tu propia herramienta de trading", "打造自己的交易工具", "나만의 트레이딩 도구 만들기"),
     ("Generate code from a recipe in your browser", "ブラウザでレシピからコードを生成", "Genera código desde una receta en el navegador", "在浏览器中根据配方生成代码", "브라우저에서 레시피로 코드 생성")),
    ("robot_poc", "/robot-pilot/", None, False,
     ("Plan a robot PoC in simulation", "ロボットのPoCをシミュレーションで", "Planificar una PoC robótica en simulación", "在仿真中规划机器人 PoC", "시뮬레이션으로 로봇 PoC 계획"),
     ("Practise teleoperation before real hardware", "実機の前に、遠隔操作を練習", "Practica la teleoperación antes del hardware real", "先练习遥操作，再上真机", "실제 하드웨어 전에 원격 조작 연습")),
    ("compare", "/trading/guides/tradingview-alternatives/", "/trading/ja/guides/tradingview-alternatives/", False,
     ("Compare platforms and approaches", "技術や道具を比べる", "Comparar plataformas y enfoques", "比较平台与方案", "플랫폼과 접근법 비교"),
     ("Check official sources before you choose", "選ぶ前に、公式情報で比較", "Consulta fuentes oficiales antes de elegir", "选择前先查官方资料", "선택 전에 공식 자료 확인")),
    ("agent_sdks", "/library/toolkit/", None, False,
     ("Find agent SDKs and frameworks", "エージェントのSDKを探す", "Encontrar SDK y frameworks de agentes", "查找智能体 SDK 与框架", "에이전트 SDK·프레임워크 찾기"),
     ("Templates grouped by framework", "フレームワーク別のテンプレート", "Plantillas agrupadas por framework", "按框架分组的模板", "프레임워크별 템플릿")),
    ("medical_robotics", "/fields/healthcare/", None, False,
     ("Evaluate medical robotics", "医療ロボティクスを検討する", "Evaluar robótica médica", "评估医疗机器人", "의료 로보틱스 검토"),
     ("Simulation recipes · research & education only", "シミュレーションのレシピ・研究と教育用途のみ", "Recetas de simulación · solo investigación y educación", "仿真配方 · 仅限研究与教育", "시뮬레이션 레시피 · 연구·교육 전용")),
]


def home_i18n(c: dict) -> dict:
    out = {lang: {} for lang in LANGS}
    for i, lang in enumerate(LANGS):
        for k, vals in STATIC_I18N.items():
            out[lang][k] = vals[i]
        out[lang]["homeCatSoon"] = SOON[i]
        out[lang]["homeCatResearchOnly"] = RESEARCH_ONLY[i]
        for key, _, names in CATS:
            out[lang][f"homeCat_{key}"] = names[i]
            n = c[f"cat_{key}"]
            out[lang][f"homeCatCount_{key}"] = UNITS[key][i].format(n=n) if n else SOON[i]
        for key, _, _, _, title, sub in GOALS:
            out[lang][f"homeGoal_{key}"] = title[i]
            out[lang][f"homeGoalSub_{key}"] = sub[i]
    return out


def i(key: str, en: str, tag: str = "span", attrs: str = "") -> str:
    return f'<{tag}{attrs} data-i18n="{key}">{html.escape(en)}</{tag}>'


def categories(c: dict) -> str:
    tiles = []
    for key, href, names in CATS:
        n = c[f"cat_{key}"]
        live = n > 0 and href
        h = href if live else "/search/?q=" + urllib.parse.quote(CAT_SEARCH.get(key, names[0].lower()))
        status = i(f"homeCatCount_{key}", UNITS[key][0].format(n=n) if n else SOON[0], attrs=' class="bsv-home-cat-status"')
        extra = i("homeCatResearchOnly", RESEARCH_ONLY[0], attrs=' class="bsv-home-cat-note"') if key == "healthcare" else ""
        tiles.append(f'<a class="bsv-home-cat{"" if live else " bsv-home-cat-soon"}" href="{h}" data-evt="home_cat_{key}" data-bsv-cat="{key}" data-live="{n if live else 0}">'
                     f'{i(f"homeCat_{key}", names[0], "strong")}{status}{extra}</a>')
    return (f'{CATS_BEGIN}\n<section class="bsv-hub bsv-home-cats" id="bsv-categories" aria-labelledby="bsv-cats-title" data-bsv-categories>'
            f'{i("homeCatsTitle", STATIC_I18N["homeCatsTitle"][0], "h2", " id=\"bsv-cats-title\"")}'
            f'<nav class="bsv-home-cat-grid" aria-labelledby="bsv-cats-title">{"".join(tiles)}</nav>'
            f'{i("homeCatsLead", STATIC_I18N["homeCatsLead"][0], "p", " class=\"bsv-home-value-note\"")}'
            f'</section>\n{CATS_END}\n')


def goals_block(audience_nav: str) -> str:
    links = []
    for key, href, href_ja, soon, title, sub in GOALS:
        inner = f'<strong>{i(f"homeGoal_{key}", title[0])}</strong>{i(f"homeGoalSub_{key}", sub[0])}'
        cls = ' class="bsv-home-goal-soon"' if soon else ""
        if href_ja:
            links.append(f'<a href="{href}"{cls} data-bsv-en data-evt="home_goal_{key}">{inner}</a>'
                         f'<a href="{href_ja}"{cls} data-bsv-ja data-evt="home_goal_{key}">{inner}</a>')
        else:
            links.append(f'<a href="{href}"{cls} data-evt="home_goal_{key}">{inner}</a>')
    return (f'{GOALS_BEGIN}\n<section class="bsv-hub bsv-home-goals" id="bsv-goals" aria-labelledby="bsv-goals-title" data-bsv-goals-section>'
            f'{i("homeGoalsTitle", STATIC_I18N["homeGoalsTitle"][0], "h2", " id=\"bsv-goals-title\"")}'
            f'{audience_nav.strip()}'
            f'<nav class="bsv-hub-ai-paths" aria-labelledby="bsv-goals-title" data-bsv-goals>{"".join(links)}</nav>'
            f'</section>\n{GOALS_END}\n')


EVT_ADD = [  # existing elements that start the funnel: add data-evt only (no copy change)
    (re.compile(r'<a class="btn-fat btn-solid" href="#packs" data-i18n="ctaBrowse"(?! data-evt)'), '<a class="btn-fat btn-solid" href="#packs" data-i18n="ctaBrowse" data-evt="home_hero_cta_browse"'),
    (re.compile(r'<a href="#trader-library" data-bsv-area="trading"(?! data-evt)'), '<a href="#trader-library" data-bsv-area="trading" data-evt="home_audience_trading"'),
    (re.compile(r'<a href="#ai-library" data-bsv-area="ai"(?! data-evt)'), '<a href="#ai-library" data-bsv-area="ai" data-evt="home_audience_ai"'),
    (re.compile(r'<a class="header-register header-register-inline" href="/register.html" data-i18n="navRegister"(?! data-evt)'), '<a class="header-register header-register-inline" href="/register.html" data-i18n="navRegister" data-evt="home_register_header"'),
]


def band() -> str:
    en = BAND_I18N["en"]
    return (f'{BAND_BEGIN}\n<section class="bsv-hub bsv-home-band" id="bsv-hero-band" aria-labelledby="bsv-hero-band-title" data-bsv-hero-band>'
            f'<h2 id="bsv-hero-band-title" data-i18n="heroBandH">{html.escape(en["heroBandH"])}</h2>'
            f'<p class="bsv-hub-lead" data-i18n="heroBandSub">{html.escape(en["heroBandSub"])}</p>'
            f'<div class="bsv-home-band-ctas"><a class="bsv-hub-button" href="#what-bsv-gives" data-evt="home_hero_cta_explore" data-i18n="heroBandCtaExplore">{html.escape(en["heroBandCtaExplore"])}</a>'
            f'<a class="bsv-hub-button bsv-hub-secondary" href="/search/" data-evt="home_hero_cta_browse_all" data-i18n="heroBandCtaBrowseAll">{html.escape(en["heroBandCtaBrowseAll"])}</a></div>'
            f'</section>\n{BAND_END}\n')


def set_page_i18n(t: str, c: dict) -> str:
    m = PAGE_I18N_RE.search(t)
    if not m:
        raise SystemExit("window.PAGE_I18N not found in index.html")
    d = json.loads(m.group(2))
    hi = home_i18n(c)
    for lang in LANGS:
        d.setdefault(lang, {}).update(BAND_I18N[lang])
        d[lang].update(hi[lang])
    return t[:m.start(2)] + json.dumps(d, ensure_ascii=False, indent=1) + t[m.end(2):]


def keep_nav(blockhtml: str) -> str:
    """When removing an old generated block, keep the audience nav it carries (it is moved, not regenerated)."""
    m = AUDIENCE_NAV_RE.search(blockhtml)
    return m.group(0) if m else ""


HEADER_INPUT_RE = re.compile(r'<input type="search" class="team-search team-search-hero" id="site-search-q"[^>]*>')
HEADER_HINT_RE = re.compile(r'<span class="search-hint visually-hidden" id="search-scope-hint"[^>]*>[^<]*</span>')


def header_search(t: str) -> str:
    """Homepage header search copy for the whole product (owner P0 10/06): existing i18n placeholder support."""
    ph, hint = STATIC_I18N["siteSearchPh"][0], STATIC_I18N["siteSearchHint"][0]
    t = HEADER_INPUT_RE.sub(lambda m: (f'<input type="search" class="team-search team-search-hero" id="site-search-q" aria-describedby="search-scope-hint" name="q" '
                                       f'placeholder="{html.escape(ph)}" data-i18n-placeholder="siteSearchPh" autocomplete="off" enterkeyhint="search" maxlength="200">'), t, count=1)
    t = HEADER_HINT_RE.sub(f'<span class="search-hint visually-hidden" id="search-scope-hint" data-i18n="siteSearchHint">{html.escape(hint)}</span>', t, count=1)
    return t


ACCESS_NOTE_RE = re.compile(r'<p><span class="bsv-hub-lock" aria-hidden="true">◈</span> .*?</p>', re.S)
ACCESS_NOTE = ('<p><span class="bsv-hub-lock" aria-hidden="true">◈</span> '
               + b("BSVで配布しているソースとダウンロードは、無料のものでもメール確認が必要です。原作者が配布しているツール（例：Position Sizer）は、原配布元のリンクからBSVのメール確認なしで入手できます。",
                   "Source and downloads hosted on BSV need a verified email, even when free. Author-hosted tools (for example Position Sizer) come from the author&#39;s own link with no BSV email verification.")
               + "</p>")


def trader_access_note(t: str) -> str:
    """Issue #4 6017081899 item 3: the Trader hub said every free tool needs a verified email. BSV-hosted gated source and
    author-hosted links have different access conditions (the Position Sizer page already says its author link needs no BSV
    verification). Copy only; the edge gate and auth are unchanged."""
    if len(ACCESS_NOTE_RE.findall(t)) != 1:
        raise SystemExit("trader hub access note not found exactly once")
    return ACCESS_NOTE_RE.sub(lambda m: ACCESS_NOTE, t, count=1)


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
    t = re.sub(re.escape(BAND_BEGIN) + r".*?" + re.escape(BAND_END) + r"\n?", "", t, flags=re.S)
    t = re.sub(re.escape(CATS_BEGIN) + r".*?" + re.escape(CATS_END) + r"\n?", lambda m: keep_nav(m.group(0)), t, flags=re.S)
    t = re.sub(re.escape(GOALS_BEGIN) + r".*?" + re.escape(GOALS_END) + r"\n?", lambda m: keep_nav(m.group(0)), t, flags=re.S)
    navs = AUDIENCE_NAV_RE.findall(t)
    if len(navs) != 1:
        raise SystemExit(f"expected exactly one audience nav, found {len(navs)}")
    t = AUDIENCE_NAV_RE.sub("", t, count=1)
    t = set_page_i18n(t, c)
    t = header_search(t)
    t = trader_access_note(t)
    t = re.sub(re.escape(CSS_BEGIN) + r".*?" + re.escape(CSS_END), "", t, flags=re.S)
    if not HERO_RE.search(t):
        raise SystemExit("hero block not found in index.html")
    t = HERO_RE.sub(lambda m: m.group(1) + band() + categories(c) + goals_block(navs[0]) + block(c), t, count=1)
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
