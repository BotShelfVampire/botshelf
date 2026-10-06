#!/usr/bin/env python3
"""Tests for the homepage value layer (build_home_value.py) on a built site.

- exactly one block, directly after the hero image and before the Trader / AI hubs
- every number shown equals a fresh count from the shipped JSON (no invented metrics)
- every link resolves to a real page in the tree; every link carries a data-evt funnel marker
- every visible string has JA and EN (es/zh/ko fall back to EN like the existing hubs)
- brand lock: hero <picture>, logo, catch / h1 copy, Trader catch, accent unchanged; no inline style,
  no new colours outside the palette already used by home-audiences css; no analytics vendor added
- no Data / Space / Biotech / Quantum / Medical promotion, no referral / IB-reward wording
- long TradingView / IB notices stay below the value layer (Trader hub)
- CSS file referenced exists and has mobile + desktop rules
usage: test_home_value.py --site DIR"""
import argparse, json, re, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_home_value as H

BRAND = [
    '<img src="/img/hero-mobile.webp?v=20260909r7" alt="BotShelf Vampire — dark shelves with gold BOTSHELF VAMPIRE lettering" width="1280" height="720">',
    '<source media="(min-width:900px)" srcset="/img/hero-desktop.webp?v=20260909r7" type="image/webp">',
    '<img src="/img/mark.jpg" width="40" height="40" alt="BotShelf Vampire">',
    '<h1 data-i18n="h1">Get ready-to-use AI teams on BotShelf Vampire.</h1>',
    '<span data-bsv-ja>トレーダーたちに捧ぐ。</span><span data-bsv-en>For the traders.</span>',
    '<span data-bsv-ja>トレードの道具を、この一か所で。</span><span data-bsv-en>Your trading toolkit, in one place.</span>',
]
VENDORS = re.compile(r"googletagmanager|google-analytics|gtag\(|plausible|umami|segment\.com|mixpanel|hotjar|clarity\.ms|posthog", re.I)
FORBIDDEN = re.compile(r"referral|紹介報酬|IB reward|rebate|キャッシュバック|quantum|量子|biotech|バイオ|space|宇宙|medical|医療|healthcare|ヘルスケア|dataset|データセット|guarantee|保証|verified by bsv|runtime-tested", re.I)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); a = ap.parse_args()
    s = Path(a.site); t = (s / "index.html").read_text(); fails = []; n = [0]
    def ok(c, m):
        n[0] += 1
        if not c: fails.append(m)
    ok(t.count(H.BEGIN) == 1 and t.count(H.END) == 1, "exactly one value block")
    i0, i1 = t.find(H.BEGIN), t.find(H.END)
    blk = t[i0:i1]
    hero_end = t.find("</picture>")
    ok(0 < hero_end < i0 < t.find('id="trader-library"') < t.find('id="ai-library"'), "order: hero -> value -> Trader hub -> AI hub")
    b0, b1 = t.find(H.BAND_BEGIN), t.find(H.BAND_END)
    ok(t.count(H.BAND_BEGIN) == 1 and t.count(H.BAND_END) == 1, "exactly one hero band")
    ok(hero_end < b0 < b1 < i0, "order: hero image -> band -> value block")
    ok(t[hero_end:b0].replace("</picture>", "").replace("</div>", "").strip() == "", "band sits directly under the hero image (no text over the image)")
    ok(t[b1 + len(H.BAND_END):i0].strip() == "", "value block directly follows the band")
    band = t[b0:b1]
    ok("<picture" not in band and "<img" not in band and "style=" not in band, "band: text only, no image, no inline style")
    ok('href="#what-bsv-gives" data-evt="home_hero_cta_explore" data-i18n="heroBandCtaExplore"' in band, "primary CTA -> #what-bsv-gives with data-evt")
    ok('href="/search/" data-evt="home_hero_cta_browse_all" data-i18n="heroBandCtaBrowseAll"' in band, "secondary CTA -> /search/ with data-evt")
    for k in ("heroBandH", "heroBandSub", "heroBandCtaExplore", "heroBandCtaBrowseAll"):
        ok(f'data-i18n="{k}"' in band, f"band uses existing i18n key {k}")
    ok("Tools, workflows and AI agents for people building what&#x27;s next." in band and "Find, compare and use practical resources for AI, trading and robotics." in band, "band EN default = owner-approved text")
    m = H.PAGE_I18N_RE.search(t); pi = json.loads(m.group(2)) if m else {}
    for lang in ("en", "ja", "es", "zh", "ko"):
        for k, v in H.BAND_I18N[lang].items():
            ok(pi.get(lang, {}).get(k) == v, f"PAGE_I18N[{lang}].{k}")
    vals = {lang: set(H.BAND_I18N[lang].values()) for lang in H.BAND_I18N}
    ok(all(not (vals[a] & vals[b]) for a in vals for b in vals if a < b), "no language reuses another language's band text")
    ok(H.BAND_I18N["ja"]["heroBandH"] == "次に作るための、ツール・ワークフロー・AIエージェント。" and H.BAND_I18N["ja"]["heroBandSub"] == "AI、トレード、ロボティクスの実用リソースを、探す・比べる・使う。", "JA = owner-approved text")
    ok(not FORBIDDEN.search(" ".join(v for d in H.BAND_I18N.values() for v in d.values())), "band: no unbacked fields / reward wording")
    for frag in BRAND:
        ok(t.count(frag) >= 1, f"brand fragment intact: {frag[:60]}")
    ok(t.find("bsv-note-tv") > i1, "TradingView / IB notices stay after the value layer")
    ok("style=" not in blk, "no inline style in block")
    ok(not VENDORS.search(t), "no analytics vendor on the homepage")
    ok(not FORBIDDEN.search(re.sub(r"<[^>]+>", " ", blk)), f"no forbidden promotion / reward wording: {FORBIDDEN.findall(re.sub(r'<[^>]+>', ' ', blk))[:5]}")
    # counts
    c = H.counts(s)
    text = re.sub(r"<[^>]+>", " ", blk)
    for k in ("trading_tools", "recipes", "recipe_platforms", "workflows", "templates", "skills", "toolkits", "toolkit_frameworks", "teams", "team_impls", "platforms_compared", "guides", "robot_curricula", "robot_recipes", "library_runtimes"):
        ok(re.search(rf"(?<![\d]){c[k]}(?![\d])", text), f"count shown: {k}={c[k]}")
    shown = {int(x) for x in re.findall(r"(?<![\w.#-])(\d+)(?![\w.-])", text)}
    allowed = {v for v in c.values() if isinstance(v, int)} | {101}  # SO-101 model name
    ok(shown <= allowed, f"every number in the block comes from a count: extra {sorted(shown - allowed)}")
    ok(c["trading_tools"] == len(json.loads((s / "trading/catalog.json").read_text())), "tools count == catalog.json")
    ok(c["library_total"] == len(json.loads((s / "library/search-index.json").read_text())) and c["library_all_free"], "library counts from search-index, all free")
    # links + funnel markers
    anchors = re.findall(r"<a\s([^>]*)>", blk)
    ok(len(anchors) >= 20, f"links present ({len(anchors)})")
    for at in anchors:
        h = re.search(r'href="([^"]*)"', at).group(1)
        ok(h.startswith("/") and not h.startswith("//"), f"root-absolute link {h}")
        p = urllib.parse.urlparse(h).path; f = s / p.lstrip("/")
        ok((f / "index.html").exists() if p.endswith("/") else f.exists(), f"link target exists {h}")
        ok(re.search(r'data-evt="home_[a-z_]+"', at), f"data-evt on {h}")
    for k in ("tools", "workflows", "agents", "templates", "research", "robotics"):
        ok(f'data-evt="home_primitive_{k}"' in blk, f"primitive {k}")
    for k in ("ai_workflow", "find_trading_tool", "build_trading_tool", "robot_practice", "compare", "agent_sdks"):
        ok(f'data-evt="home_goal_{k}"' in blk, f"goal {k}")
    for k in ("ai", "trading", "robotics"):
        ok(f'data-evt="home_field_{k}"' in blk, f"field {k}")
    for e in ("home_hero_cta_browse", "home_hero_cta_explore", "home_hero_cta_browse_all", "home_audience_trading", "home_audience_ai", "home_register_header"):
        ok(t.count(f'data-evt="{e}"') == 1, f"existing funnel entry marked once: {e}")
    # bilingual
    ja, en = blk.count("data-bsv-ja"), blk.count("data-bsv-en")
    ok(ja == en and ja >= 30, f"JA/EN pairs balanced ({ja}/{en})")
    # CSS
    m = re.search(r'href="/css/(home-value\.[0-9a-f]{8}\.css)"', t)
    ok(m and (s / "css" / m.group(1)).exists(), "value css linked and shipped")
    if m:
        css = (s / "css" / m.group(1)).read_text()
        ok("@media(max-width:640px)" in css and "@media(max-width:950px)" in css, "mobile + tablet rules")
        cols = set(re.findall(r"#[0-9a-fA-F]{3,6}\b", css))
        pal = set(re.findall(r"#[0-9a-fA-F]{3,6}\b", next((s / "css").glob("home-audiences.*.css")).read_text()))
        ok(cols <= pal, f"no new colours: {cols - pal}")
    # idempotent
    before = t
    H.apply(s)
    ok((s / "index.html").read_text() == before, "idempotent rebuild")
    print(json.dumps({"test": "home_value", "checks": n[0], "failures": len(fails), "fail": fails[:12]}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
