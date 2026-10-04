#!/usr/bin/env python3
"""Integrate trader-toolkit/ and ai-toolkit/ into the EXISTING live BSV categories.

Reads the repo catalogs (trader-toolkit/catalog.json, ai-toolkit/catalog.json) plus
scripts/site/toolkit-site-copy.json and writes into a checked-out live-site tree:

Trader (existing /trading/ category, no new category):
  /trading/build/index.html                 public hub: Build your own chart tool
  /trading/build/toolkit.v1.json            public metadata (no source bodies)
  /trading/tools/bsv-<id>.html              public summary pages
  /trading/items/bsv-<id>.html              source pages   (edge gate: email-verified session)
  /trading/downloads/bsv-<id>.zip           source + LICENSE (edge gate)
AI (existing /library/ category, no new category):
  /library/toolkit/index.html               public hub organised by job and by framework
  /library/toolkit/<id>/index.html          public summary pages
  /library/source/<id>.html | .zip          source (edge gate; path added to free-session-gate)

Entry points are injected between BSV-TOOLKIT markers in /trading/index.html and
/library/index.html. Re-running is idempotent. Source bodies are never written to
public paths. No status is upgraded: catalog status is shown as-is.

Usage: python3 scripts/site/build_live_toolkit.py --site /path/to/site [--repo .]
"""
from __future__ import annotations

import argparse, hashlib, html, io, json, re, subprocess, urllib.parse, zipfile
from pathlib import Path

VER = "v20261003"
ORIGIN = "https://botshelfvampire.com"
GATE_PATH = "/library/source/*"
REPO = Path(__file__).resolve().parents[2]
# CSS/JS are served with immutable cache headers: names carry a content hash.
ASSET = {}
TEXT_EXT = {".pine", ".mq5", ".mq4", ".cs", ".cpp", ".lipi", ".txt", ".java", ".js", ".json", ".md", ".py", ".html", ".mjs"}
ZIP_DATE = (2026, 10, 3, 0, 0, 0)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def both(d: dict, tag: str = "span", cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} data-lang="en"{c}>{esc(d["en"])}</{tag}><{tag} data-lang="ja"{c}>{esc(d["ja"])}</{tag}>'


def lib_both(d: dict, tag: str = "span", cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} data-lang-show="en"{c}>{esc(d["en"])}</{tag}><{tag} data-lang-show="ja" hidden{c}>{esc(d["ja"])}</{tag}>'


def T(en, ja):
    return {"en": en, "ja": ja}


def files_for(repo: Path, rel: str) -> list[Path]:
    p = repo / rel
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.is_file() and f.suffix in TEXT_EXT)
    return [p]


def det_zip(entries: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:
            zi = zipfile.ZipInfo(name, ZIP_DATE)
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
    return buf.getvalue()


def write(path: Path, data, binary=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def replace_block(text: str, marker: str, block: str, anchor: str, before: bool = True) -> str:
    start, end = f"<!-- BSV-TOOLKIT:{marker} -->", f"<!-- /BSV-TOOLKIT:{marker} -->"
    wrapped = start + block + end
    if start in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: wrapped, text, count=1, flags=re.S)
    i = text.find(anchor)
    if i < 0:
        raise SystemExit(f"anchor not found for {marker}: {anchor[:60]}")
    return text[:i] + wrapped + text[i:] if before else text[: i + len(anchor)] + wrapped + text[i + len(anchor):]


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------
PLATFORM_OF = {"Pine/MQL5/MQL4/cTrader/Bookmap/NinjaTrader/Quantower/Sierra Chart/ProRealTime/GoCharting/MotiveWave/Vela/JForex/TradeStation/ATAS/AmiBroker/thinkorswim/Tradovate/backtrader/Backtesting.py/NautilusTrader": ["TradingView", "MT5", "MT4", "cTrader", "Bookmap", "NinjaTrader", "Quantower", "Sierra Chart", "ProRealTime", "GoCharting", "MotiveWave", "Vela", "JForex", "TradeStation", "ATAS", "AmiBroker", "thinkorswim", "Tradovate", "backtrader", "Backtesting.py", "NautilusTrader"]}
STEPS = [
    T("Pick one job", "目的を1つ決める"), T("Pick blocks", "ブロックを選ぶ"), T("Generate a starter", "ひな形を生成"),
    T("Paste / import", "貼り付け・取り込み"), T("Verify", "検証する"), T("Customize", "改造する"), T("Publish honestly", "正直に公開"),
]
STEP_TXT = [
    T("Overlay, dashboard, scanner, alert, study or your own web chart. Start with one job you can verify — not twenty signals.",
      "重ね表示・ダッシュボード・スキャナー・アラート・オシレーター・自作Webチャートから1つ。最初から20個のシグナルを入れず、検証できる1つから始めます。"),
    T("A recipe is JSON: each block has an id, a type (for example indicator.ema, signal.cross, visual.table, alert.condition) and params. Later blocks refer to earlier ids.",
      "レシピはJSONです。各ブロックにid・type（indicator.ema、signal.cross、visual.table、alert.conditionなど）・paramsがあり、後のブロックが前のidを参照します。"),
    T("Run the generator for Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, NinjaTrader 8 or Quantower — or take the pre-generated starters on each recipe page. Unsupported blocks remain as visible TODO comments.",
      "ジェネレーターでPine v6・MQL5・MQL4・cTrader（C#／Python）・Bookmap（Python）・NinjaTrader 8・Quantower・Sierra Chart（ACSIL）・ProRealTime・GoCharting（Lipi）・MotiveWave（Java）・Vela（JavaScript）・JForex（Java）・TradeStation（EasyLanguage）・ATAS（C#）・AmiBroker（AFL）・thinkorswim（thinkScript）・Tradovate（JavaScript）・backtrader（Python）・Backtesting.py（Python）・NautilusTrader（Python）向けに出力します。各レシピのページにある生成済みのひな形も使えます。未対応のブロックはTODOコメントとして残ります。"),
    T("TradingView: new Pine indicator → paste → save → add to chart. MT5 / MT4: MetaEditor custom indicator → compile. cTrader: Algo custom indicator (C# or Python) → build. Bookmap: load the Python add-on. Vela: your own browser chart.",
      "TradingView：新規Pineインジケーターに貼り付けて保存しチャートに追加。MT5・MT4：MetaEditorでカスタムインジケーターとしてコンパイル。cTrader：Algoでカスタムインジケーター（C#またはPython）としてビルド。Bookmap：Pythonアドオンとして読み込み。Vela：自分のブラウザーチャート。"),
    T("Check source/version, enough history, symbol and timezone assumptions, repainting/lookahead, session handling, alert frequency and edge-case parameters. A compile pass is not proof of trading value.",
      "ソースとバージョン、十分な過去データ、銘柄・タイムゾーンの前提、リペイント・先読み、時間帯の扱い、アラートの頻度、極端なパラメーターを確認します。コンパイルが通っても売買の価値の証明にはなりません。"),
    T("Swap EMA lengths, add higher-timeframe data, change thresholds, add ATR bands or a session gate, add webhook-ready alerts, split one big tool into an overlay + a scanner.",
      "EMAの期間を変える、上位足のデータを足す、しきい値を変える、ATRバンドや時間帯の条件を足す、Webhookアラートを足す、大きなツールを重ね表示とスキャナーに分ける。"),
    T("If you list the result on BSV, state original/adapted source, platform/version, prerequisites, what is tested, what is not, limitations — and no unsupported performance claims.",
      "BSVに出品するなら、オリジナルか改変か、プラットフォームとバージョン、前提条件、検証済みの範囲と未検証の範囲、制約を書きます。根拠のない成績は書きません。"),
]
HTF_REAL = ("backtrader", "backtesting-py", "nautilus", "tradovate")  # real higher-timeframe values; must match htfRealTargets() in render.mjs
HTF_IDIOM = ("pine-v6", "mql5", "mql4", "ninjatrader", "ctrader", "amibroker", "thinkscript")  # documented closed-bar idiom, static check only; must match htfIdiomTargets() in render.mjs
TARGETS = [("pine-v6", "TradingView · Pine v6", ".pine"), ("mql5", "MT5 · MQL5", ".mq5"), ("ctrader", "cTrader · C#", ".cs"),
           ("mql4", "MT4 · MQL4", ".mq4"), ("ctrader-python", "cTrader · Python", ".py"), ("bookmap-python", "Bookmap · Python", ".py"),
           ("ninjatrader", "NinjaTrader 8 · NinjaScript", ".cs"), ("quantower", "Quantower · C#", ".cs"),
           ("sierra-acsil", "Sierra Chart · ACSIL C++", ".cpp"), ("prorealtime", "ProRealTime · ProBuilder", ".txt"),
           ("gocharting-lipi", "GoCharting · Lipi", ".lipi"), ("motivewave", "MotiveWave · Java", ".java"), ("vela", "Vela · JavaScript", ".js"), ("jforex", "JForex · Java", ".java"), ("easylanguage", "TradeStation · EasyLanguage", ".txt"), ("atas", "ATAS · C#", ".cs"), ("amibroker", "AmiBroker · AFL", ".afl"), ("thinkscript", "thinkorswim · thinkScript", ".ts"), ("tradovate", "Tradovate · JavaScript", ".js"), ("backtrader", "backtrader · Python", ".py"), ("backtesting-py", "Backtesting.py · Python", ".py"), ("nautilus", "NautilusTrader · Python", ".py")]


def trader_records(repo: Path, copy: dict) -> list[dict]:
    cat = json.loads((repo / "trader-toolkit/catalog.json").read_text())
    out = []
    for e in cat["entries"]:
        c = copy["trader"].get(e["id"], {})
        copy["trader_types"].setdefault(e["type"], T(e["type"], e["type"]))
        copy["status"].setdefault(e["status"], T(e["status"] + " — not runtime verified", e["status"] + "（実行検証なし）"))
        rel = e["path"]
        platforms = PLATFORM_OF.get(e["platform"], [e["platform"]])
        files = [f for f in files_for(repo, rel)]
        readme = None
        pdir = (repo / rel) if (repo / rel).is_dir() else (repo / rel).parent
        if (pdir / "README.md").exists() and pdir.name != "docs":
            readme = (pdir / "README.md").read_text()
        refs = sorted(set(re.findall(r"https?://[^\s)<>`]+", readme or "")))
        gated = e["type"] not in ("guide", "integration-guide")
        if e["type"] == "starter-app" or e["type"] == "integration-guide":
            pass
        out.append({
            "id": e["id"], "slug": "bsv-" + e["id"], "title": e["title"], "platforms": platforms, "platform_label": e["platform"],
            "type": e["type"], "status": e["status"], "featured": bool(e.get("featured")), "repo_path": rel,
            "summary": c.get("summary", T(e["title"], e["title"])), "use": c.get("use"), "refs": refs,
            "files": files if gated else [], "gated": gated, "readme": readme,
        })
    return out


def recipe_records(repo: Path, copy: dict) -> list[dict]:
    cat = json.loads((repo / "trader-toolkit/catalog.json").read_text())
    gen = repo / "trader-toolkit/generator/render.mjs"
    out = []
    for name in cat.get("recipes", []):
        p = repo / f"trader-toolkit/recipes/{name}.json"
        if not p.exists():
            raise SystemExit(f"catalog lists missing recipe {name}")
        r = json.loads(p.read_text())
        outputs = []
        for tgt, label, ext in TARGETS:
            res = subprocess.run(["node", str(gen), str(p), "--target", tgt], capture_output=True, text=True)
            if res.returncode != 0:
                raise SystemExit(f"generator failed for {name}/{tgt}: {res.stderr[:300]}")
            todos = len(re.findall(r"TODO", res.stdout))
            outputs.append({"target": tgt, "label": label, "file": f"{name}.{tgt}{ext}", "code": res.stdout, "todos": todos})
        ja = copy["recipes"].get(name, {}).get("ja", r.get("description", ""))
        out.append({
            "id": "recipe-" + name, "slug": "bsv-recipe-" + name, "recipe": name, "title": r["name"],
            "platforms": ["TradingView", "MT5", "MT4", "cTrader", "Bookmap", "NinjaTrader", "Quantower", "Sierra Chart", "ProRealTime", "GoCharting", "MotiveWave", "Vela", "JForex", "TradeStation", "ATAS", "AmiBroker", "thinkorswim", "Tradovate", "backtrader", "Backtesting.py", "NautilusTrader"], "platform_label": "Recipe → Pine/MQL5/MQL4/cTrader/Bookmap/NinjaTrader/Quantower/Sierra Chart/ProRealTime/GoCharting/MotiveWave/Vela/JForex/TradeStation/ATAS/AmiBroker/thinkorswim/Tradovate/backtrader/Backtesting.py/NautilusTrader",
            "type": "recipe", "status": "STRUCTURAL", "featured": False, "repo_path": f"trader-toolkit/recipes/{name}.json",
            "summary": T(r.get("description", r["name"]), ja), "overlay": r.get("overlay"),
            "blocks": [(b["id"], b["type"]) for b in r["blocks"]], "outputs": outputs, "json": p.read_text(),
            "gated": True, "files": [p], "refs": [],
        })
    return out


def trader_shell(site: Path, title: str, desc: str, canonical: str, body: str, robots: str = "index,follow", extra_head: str = "") -> str:
    idx = (site / "trading/index.html").read_text()
    hdr = idx[idx.find('<header class="site-header">'): idx.find("</header>") + 9]
    hdr = hdr.replace(' class="active"', "")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><base href="/trading/">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">'
        f'<meta name="robots" content="{robots}"><link rel="canonical" href="{ORIGIN}{canonical}">'
        f'<link rel="stylesheet" href="/trading/assets/library.css"><link rel="stylesheet" href="{ASSET["tcss"]}">'
        f'{extra_head}<script src="{ASSET["tjs"]}" defer></script></head><body class="bsv-build">'
        '<a class="skip" href="#main">Skip to content</a>' + hdr + f'<main id="main">{body}</main>'
        '<footer class="site-footer"><div class="container"><p data-lang="en">Original BSV starter source (MIT). Platform names belong to their owners; BSV is not affiliated with or endorsed by them. Source prepared is not runtime verified. Educational and research use; not investment advice; no profitability is promised.</p>'
        '<p data-lang="ja">BSVオリジナルのスターターコード（MITライセンス）。各プラットフォーム名は各社のものであり、提携や推奨を示すものではありません。ソースを用意したことは実行検証済みを意味しません。学習・研究のための情報提供で、投資助言ではなく、収益を保証するものでもありません。</p></div></footer>'
        '<div id="toast" role="status" class="toast" hidden></div></body></html>'
    )


def status_badge(copy, status):
    s = copy["status"][status]
    cls = "ok" if status == "CI_PASS" else "warn"
    return f'<span class="bb-status bb-{cls}" data-status="{esc(status)}">{both(s)}</span>'


def type_label(copy, t):
    return both(copy["trader_types"][t])


def trader_card(copy, r) -> str:
    plats = " · ".join(r["platforms"])
    href = f"/trading/tools/{r['slug']}.html" if r["id"] != "trader-build-own-chart" else "/trading/build/#path"
    search = " ".join([r["title"], plats, r["type"], r["summary"]["en"], r["summary"]["ja"]]).lower()
    feat = '<span class="bb-flag">FEATURED</span>' if r["featured"] else ""
    return (
        f'<article class="bb-card" data-platforms="{esc("|".join(r["platforms"]))}" data-type="{esc(r["type"])}" data-status="{esc(r["status"])}" data-search="{esc(search)}">'
        f'<div class="bb-meta"><span>{esc(plats)}</span>{feat}</div>'
        f'<h3><a href="{href}">{esc(r["title"])}</a></h3>{both(r["summary"], "p")}'
        f'<div class="bb-tags"><span class="bb-type">{type_label(copy, r["type"])}</span>{status_badge(copy, r["status"])}<span class="bb-orig">ORIGINAL · MIT</span></div></article>'
    )


def build_trader(site: Path, repo: Path, copy: dict) -> dict:
    recs = trader_records(repo, copy)
    recipes = recipe_records(repo, copy)
    allr = recs + recipes
    platforms = []
    for r in allr:
        for p in r["platforms"]:
            if p not in platforms and p != "BSV":
                platforms.append(p)
    types = [t for t in copy["trader_types"] if any(r["type"] == t for r in allr)]
    statuses = [s for s in copy["status"] if any(r["status"] == s for r in allr)]
    lic = (repo / "LICENSE").read_bytes()

    # ---- gated source pages + zips
    for r in allr:
        if not r["gated"]:
            continue
        blocks, zentries = [], []
        if r["type"] == "recipe":
            srcs = [(f"{r['recipe']}.json", r["json"], "Recipe JSON")] + [(o["file"], o["code"], o["label"] + f" · TODO×{o['todos']}") for o in r["outputs"]]
        else:
            base = (repo / r["repo_path"]) if (repo / r["repo_path"]).is_dir() else (repo / r["repo_path"]).parent
            srcs = [(str(f.relative_to(base)), f.read_text(), f.suffix.lstrip(".")) for f in r["files"]]
            if r["readme"] and not any(n == "README.md" for n, _, _ in srcs):
                srcs.append(("README.md", r["readme"], "md"))
        for i, (name, code, label) in enumerate(srcs):
            cid = f"{r['slug']}-{i}"
            sha = hashlib.sha256(code.encode()).hexdigest()
            blocks.append(
                f'<details class="source-block" {"open" if i == 0 else ""}><summary>{esc(name)} · {esc(label)} · {len(code.encode())} bytes</summary>'
                f'<div class="source-toolbar"><button class="btn small-btn" data-bb-copy="{cid}">{both(T("Copy code", "コードをコピー"))}</button></div>'
                f'<pre id="{cid}" tabindex="0"><code>{esc(code)}</code></pre><div class="source-toolbar hash">SHA256 {sha}</div></details>'
            )
            zentries.append((f"{r['slug']}/{name}", code.encode()))
        zentries.append((f"{r['slug']}/LICENSE.txt", lic))
        write(site / f"trading/downloads/{r['slug']}.zip", det_zip(zentries), binary=True)
        body = (
            f'<div class="container detail"><div class="breadcrumb"><a href="/trading/">← Traders Library</a> / <a href="/trading/build/">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a> / {esc(r["title"])}</div>'
            f'<article class="prose"><div class="badges"><span class="badge">{esc(" · ".join(r["platforms"]))}</span><span class="badge license">MIT</span><span class="badge">{type_label(copy, r["type"])}</span></div>'
            f'<h1 class="detail-title">{esc(r["title"])}</h1>{both(r["summary"], "p", "detail-lead")}'
            f'<p>{status_badge(copy, r["status"])} <span class="bb-orig">ORIGINAL BSV SOURCE</span></p>'
            f'<p><a class="btn primary" href="/trading/downloads/{r["slug"]}.zip">{both(T("Download ZIP (source + LICENSE)", "ZIPを取得（ソース＋ライセンス）"))}</a></p>'
            + "".join(blocks)
            + f'<details class="source-block"><summary>{both(T("Full license (MIT)", "ライセンス全文（MIT）"))}</summary><pre>{esc(lic.decode())}</pre></details>'
            f'<p class="small"><a href="/trading/tools/{r["slug"]}.html">{both(T("← Back to the summary page", "← 解説ページへ戻る"))}</a></p></article></div>'
        )
        write(site / f"trading/items/{r['slug']}.html",
              trader_shell(site, f"{r['title']} — source · BotShelf Vampire", r["summary"]["en"], f"/trading/tools/{r['slug']}.html", body, robots="noindex,nofollow"))

    # ---- public summary pages
    for r in allr:
        if r["id"] == "trader-build-own-chart":
            continue
        use = r.get("use")
        if not use and r["type"] == "copy-paste-code":
            use = {"en": ["Open code (free email verification) and copy the starter.", f"Create a new script/indicator in {r['platforms'][0]} and paste it.", "Compile or validate inside the platform; fix anything your version rejects.", "Check it on historical data and a non-live workflow before adapting it."],
                   "ja": ["メール確認（無料）でコードを開き、ひな形をコピーします。", f"{r['platforms'][0]}で新しいスクリプト・インジケーターを作って貼り付けます。", "プラットフォーム内でコンパイル・検証し、お使いのバージョンで通らない箇所を直します。", "過去データと実運用ではない環境で確認してから改造します。"]}
        if not use and r["type"] == "starter-app":
            use = {"en": ["Create a Vite project and install Vela from its official package (npm install @luxalgo/vela); review its license.", "Copy the BSV starter files (index.html, starter.js, package.json).", "Replace the sample bars with your own OHLCV data: { time (epoch ms), open, high, low, close, volume }.", "Run npm run dev, then add indicators, drawings or a reviewed scripting engine one at a time."],
                   "ja": ["Viteのプロジェクトを作り、Velaを公式パッケージから入れます（npm install @luxalgo/vela）。ライセンスも確認します。", "BSVのスターター（index.html・starter.js・package.json）をコピーします。", "サンプルのローソク足を自分のOHLCVデータ（time〔エポックミリ秒〕・open・high・low・close・volume）に置き換えます。", "npm run devで起動し、指標・描画・確認済みのスクリプトエンジンを1つずつ足します。"]}
        if not use and r["type"] == "recipe":
            use = {"en": ["Open code (free email verification) to get the recipe JSON and twenty-two pre-generated starters (Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart ACSIL, ProRealTime, GoCharting Lipi, MotiveWave Java, Vela JavaScript, JForex Java, TradeStation EasyLanguage, ATAS C#, AmiBroker AFL, thinkorswim thinkScript, Tradovate JavaScript, backtrader Python, Backtesting.py Python, NautilusTrader Python).", "Paste the starter for your platform, compile it there and resolve every TODO marker.", "Or edit the recipe JSON and re-run the generator yourself."],
                   "ja": ["メール確認（無料）でレシピJSONと生成済みのひな形22種類（Pine v6・MQL5・MQL4・cTrader C#・cTrader Python・Bookmap Python・NinjaTrader 8・Quantower・Sierra Chart（ACSIL）・ProRealTime・GoCharting（Lipi）・MotiveWave（Java）・Vela（JavaScript）・JForex（Java）・TradeStation（EasyLanguage）・ATAS（C#）・AmiBroker（AFL）・thinkorswim（thinkScript）・Tradovate（JavaScript）・backtrader（Python）・Backtesting.py（Python）・NautilusTrader（Python））を開きます。", "使うプラットフォーム用のひな形を貼り付けてコンパイルし、TODOをすべて解消します。", "レシピJSONを編集してジェネレーターを自分で実行し直すこともできます。"]}
        sections = []
        if r["type"] == "recipe":
            rows = "".join(f'<tr><td><code>{esc(i)}</code></td><td><code>{esc(t)}</code></td></tr>' for i, t in r["blocks"])
            sections.append(f'<h2>{both(T("Blocks in this recipe", "このレシピのブロック"))}</h2><table class="qa-table"><thead><tr><th>id</th><th>type</th></tr></thead><tbody>{rows}</tbody></table>')
            if '"timeframeRef"' in r["json"]:  # higher-timeframe honesty notice (2026-10-04 correction)
                real = [lab for t, lab, _ in TARGETS if t in HTF_REAL]
                idiom = [lab for t, lab, _ in TARGETS if t in HTF_IDIOM]
                rest = len(TARGETS) - len(real) - len(idiom)
                sections.append(f'<h2 id="higher-timeframe">{both(T("Higher timeframe: where it is computed", "上位足：計算する出力先"))}</h2>'
                                f'<p>{both(T("Blocks marked with a higher timeframe are computed from closed higher-timeframe bars only (no repaint, no lookahead) on " + ", ".join(real) + ", checked by BSV inside those libraries on synthetic bars. On " + ", ".join(idiom) + " they read the last closed higher-timeframe bar with each platform\'s officially documented idiom (Pine: request.security with expr[1] and lookahead_on; MQL5/MQL4: iBarShift + 1; NinjaTrader: AddDataSeries with Calculate.OnBarClose), and stop with an error when the chart timeframe is not lower. BSV checks that pattern statically but cannot run those platforms (UNTESTED_RUNTIME): compile and compare on your platform. On the other " + str(rest) + " targets they are left as unsupported stubs with a TODO line (empty value, false signal), never computed on the chart timeframe.", "上位足を指定したブロックは、" + "・".join(real) + " では確定した上位足だけから計算します（描き直し・先読みなし。BSVがそれぞれのライブラリ内で合成データを使って確認）。" + "・".join(idiom) + " では、各プラットフォームの公式ドキュメントにある方法（Pine：expr[1]とlookahead_onを付けたrequest.security、MQL5/MQL4：iBarShift＋1、NinjaTrader：Calculate.OnBarCloseでのAddDataSeries）で直前に確定した上位足を読み、表示中の足が上位足より短くなければエラーで止まります。BSVはこの形を静的に確認していますが、これらのプラットフォームでは実行していません（UNTESTED_RUNTIME）。ご自身の環境でコンパイルして確かめてください。ほかの" + str(rest) + "の出力先では、TODO付きの未対応スタブ（値は空、シグナルはfalse）のままにしており、表示中の足で計算することはありません。"))}</p>'
                                f'<p class="small">{both(T("Correction (2026-10-04): earlier starters for this recipe computed these blocks on the chart timeframe without saying so. Download the starters again.", "訂正（2026-10-04）：このレシピの以前のひな形は、何の注記もなくこれらのブロックを表示中の足で計算していました。ひな形をダウンロードし直してください。"))} <a href="/trading/build/coverage.json">coverage.json</a></p>')
            orows = "".join(
                f'<tr><td>{esc(o["label"])}</td><td>{o["todos"]}</td></tr>' for o in r["outputs"])
            sections.append(f'<h2>{both(T("Pre-generated starters", "生成済みのひな形"))}</h2>'
                            f'<p>{both(T("Generated by the BSV generator from this recipe. TODO markers are blocks the target cannot express yet — resolve them before use.", "このレシピからBSVジェネレーターで生成しました。TODOは出力先でまだ表現できないブロックです。使う前に解消してください。"))}</p>'
                            f'<table class="qa-table"><thead><tr><th>{both(T("Target", "出力先"))}</th><th>{both(T("TODO markers", "TODOの数"))}</th></tr></thead><tbody>{orows}</tbody></table>')
        if use:
            sections.append(f'<h2>{both(T("How to use", "使い方"))}</h2><ol data-lang="en">' + "".join(f"<li>{esc(x)}</li>" for x in use["en"]) + '</ol><ol data-lang="ja">' + "".join(f"<li>{esc(x)}</li>" for x in use["ja"]) + "</ol>")
        ver_rows = [
            (T("Source", "出典"), T("ORIGINAL BSV source, MIT license", "BSVオリジナルのソース・MITライセンス")),
            (T("Catalog status", "カタログ上の状態"), copy["status"][r["status"]]),
            (T("Compile / build on the platform", "プラットフォームでのコンパイル・ビルド"), T("Not performed by BSV", "BSVでは未実施")),
            (T("Backtest / demo / live run", "バックテスト・デモ・実運用"), T("Not performed", "未実施")),
            (T("Order placement", "発注機能"), T("None — visual/alert starter only", "なし（表示・アラートのみ）")),
        ]
        if r["type"] == "integration-guide":
            ver_rows = [(T("Source", "出典"), T("BSV integration notes (no adapter code yet)", "BSVの連携メモ（アダプターのコードはまだありません）")),
                        (T("Catalog status", "カタログ上の状態"), copy["status"][r["status"]]),
                        (T("BSV runtime adapter", "BSVの実行用アダプター"), T("Not implemented", "未実装"))]
        sections.append(f'<h2>{both(T("Verification scope", "確認の範囲"))}</h2><table class="qa-table"><tbody>' + "".join(f"<tr><td>{both(a)}</td><td>{both(b)}</td></tr>" for a, b in ver_rows) + "</tbody></table>")
        if r["refs"]:
            sections.append(f'<h2>{both(T("Official references", "公式資料"))}</h2><ul>' + "".join(f'<li><a href="{esc(u)}" rel="noopener noreferrer" target="_blank">{esc(u)}</a></li>' for u in r["refs"]) + "</ul>")
        if r["files"]:
            names = []
            base = (repo / r["repo_path"]) if (repo / r["repo_path"]).is_dir() else (repo / r["repo_path"]).parent
            for f in r["files"]:
                names.append(f"{f.relative_to(base)} · {f.stat().st_size} bytes")
            if r["type"] == "recipe":
                names += [f'{o["file"]} · {len(o["code"].encode())} bytes' for o in r["outputs"]]
            sections.append(f'<h2>{both(T("Files", "ファイル"))}</h2><ul class="bb-files">' + "".join(f"<li><code>{esc(n)}</code></li>" for n in names) + "</ul>")
        action = ""
        if r["gated"]:
            nxt = f"/trading/items/{r['slug']}.html"
            action = (f'<p class="trader-tool-action-row"><a class="btn primary" href="/trading/register.html?next={esc(nxt.replace("/", "%2F"))}" data-source-access="{r["slug"]}">'
                      f'{both(T("Open code — free email verification", "メール確認してコードを開く（無料）"))}</a></p>'
                      f'<p class="small">{both(T("Summaries are public. Viewing, copying and downloading BSV-provided source requires free email verification.", "解説は登録なしで読めます。BSVが提供するコードの閲覧・コピー・ダウンロードには無料のメール確認が必要です。"))}</p>')
        lede_extra = ""
        if r["id"] == "vela-custom-chart":
            lede_extra = f'<p class="bb-callout">{both(T("Vela is the custom-chart path: you own the page, the data source, the theme, indicators and drawings, and how the chart is embedded in your own product.", "Velaは「チャートそのものを作る」道です。ページ・データの取得元・テーマ・指標・描画・自分の製品への埋め込み方を自分で決められます。"))}</p>'
        if r["id"] == "openmarkets-data":
            lede_extra = f'<p class="bb-callout">{both(T("Not a chart scripting language. Use it as a read-only data or MCP research input, for example feeding your own Vela chart after you build an adapter.", "チャート用のスクリプト言語ではありません。読み取り専用のデータ・MCPリサーチの入力として使い、アダプターを作れば自作のVelaチャートにデータを渡せます。"))}</p>'
        body = (
            f'<div class="container detail"><div class="breadcrumb"><a href="/trading/">← Traders Library</a> / <a href="/trading/build/">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a> / {esc(r["title"])}</div>'
            f'<article class="prose"><div class="badges"><span class="badge">{esc(" · ".join(r["platforms"]))}</span><span class="badge license">MIT</span><span class="badge">{type_label(copy, r["type"])}</span></div>'
            f'<h1 class="detail-title">{esc(r["title"])}</h1>{both(r["summary"], "p", "detail-lead")}'
            f'<p>{status_badge(copy, r["status"])} <span class="bb-orig">ORIGINAL BSV SOURCE</span></p>{lede_extra}{action}'
            + "".join(sections) + "</article></div>"
        )
        write(site / f"trading/tools/{r['slug']}.html",
              trader_shell(site, f"{r['title']} ({' / '.join(r['platforms'])}) — Build your own chart tool · BotShelf Vampire", r["summary"]["en"], f"/trading/tools/{r['slug']}.html", body))

    # ---- hub
    sel = lambda sid, label, opts: (f'<label class="bb-sel"><span class="sr">{esc(label)}</span><select id="{sid}" aria-label="{esc(label)}">' + "".join(opts) + "</select></label>")
    popts = ['<option value="" data-en="All platforms" data-ja="すべての環境">All platforms</option>'] + [f'<option value="{esc(p)}">{esc(p)}</option>' for p in platforms]
    topts = ['<option value="" data-en="All types" data-ja="すべての種類">All types</option>'] + [f'<option value="{esc(t)}" data-en="{esc(copy["trader_types"][t]["en"])}" data-ja="{esc(copy["trader_types"][t]["ja"])}">{esc(copy["trader_types"][t]["en"])}</option>' for t in types]
    sopts = ['<option value="" data-en="Any test status" data-ja="すべての検証状態">Any test status</option>'] + [f'<option value="{esc(s)}" data-en="{esc(copy["status"][s]["en"])}" data-ja="{esc(copy["status"][s]["ja"])}">{esc(copy["status"][s]["en"])}</option>' for s in statuses]
    steps = "".join(f'<li><strong>{both(STEPS[i])}</strong>{both(STEP_TXT[i], "p")}</li>' for i in range(7))
    featured = [r for r in recs if r["featured"] and r["id"] != "trader-build-own-chart"]
    paths = "".join(f'<a class="bb-path" href="/trading/tools/{r["slug"]}.html"><small>{esc(" · ".join(r["platforms"]))}</small><strong>{esc(r["title"])}</strong>{both(r["summary"], "span")}</a>' for r in featured)
    comp = (repo / "trader-toolkit/docs/compatibility.md").read_text()
    rows = [l for l in comp.splitlines() if l.startswith("| ") and not l.startswith("| Platform") and not l.startswith("| ---")]
    crow = ""
    for l in rows:
        cells = [c.strip() for c in l.strip("|").split("|")]
        crow += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>"
    cards = "".join(trader_card(copy, r) for r in allr)
    hub = (
        '<section class="container hero bb-hero"><div><div class="eyebrow">TRADERS LIBRARY / BUILD YOUR OWN CHART TOOL</div>'
        f'<h1>{both(T("Build your own chart tool.", "自分のチャートツールを作る。"))}</h1>'
        f'{both(T("Recipes, blocks and a code generator for indicators, dashboards, scanners, alerts and your own web chart — with minimal coding.", "インジケーター・ダッシュボード・スキャナー・アラート、そして自分のWebチャートまで。レシピ・ブロック・コード生成で、最小限のコーディングで作れます。"), "p", "lead")}'
        f'{both(T("Everything here is ORIGINAL BSV source under the MIT license. Nothing has been runtime tested by BSV yet — each item says exactly what was checked.", "ここにあるものはすべてBSVオリジナルのソース（MITライセンス）です。BSVではまだ実行検証をしていません。各項目に確認した範囲を明記しています。"), "p", "small")}'
        f'{both(T("Summaries are public. Viewing, copying and downloading the source requires free email verification.", "解説は登録なしで読めます。コードの閲覧・コピー・ダウンロードには無料のメール確認が必要です。"), "p", "small")}</div>'
        f'<aside class="hero-stats"><div class="stat-total"><strong>{len(allr)}</strong>{both(T("build assets", "作るための素材"))}</div><div class="stat-lines">'
        f'<div>{both(T("Platforms", "プラットフォーム"))}<b>{len(platforms)}</b></div><div>{both(T("Recipes", "レシピ"))}<b>{len(recipes)}</b></div><div>{both(T("Runtime-tested by BSV", "BSVでの実行検証済み"))}<b>0</b></div></div></aside></section>'
        f'<div class="container subnav"><a class="chip" href="#path">{both(T("7-step path", "7つの手順"))}</a><a class="chip" href="#paths">{both(T("Start points", "始め方"))}</a><a class="chip" href="#catalog">{both(T("All build assets", "すべての素材"))}</a><a class="chip" href="#compat">{both(T("Platform compatibility", "対応状況"))}</a><a class="chip" href="/trading/">{both(T("Traders Library", "Traders Library"))}</a></div>'
        f'<section class="container bb-section" id="path"><h2>{both(T("The path: idea → working tool", "アイデアから動くツールまで"))}</h2><ol class="bb-steps">{steps}</ol></section>'
        f'<section class="container bb-section" id="paths"><h2>{both(T("Pick a start point", "始め方を選ぶ"))}</h2><div class="bb-paths">{paths}</div></section>'
        f'<section class="container bb-section" id="catalog"><div class="collection-header"><h2>{both(T("All build assets", "すべての素材"))}</h2><span class="results" id="bb-count" aria-live="polite">{len(allr)}</span></div>'
        f'<div class="filters bb-filters"><label class="search-wrap"><span aria-hidden="true">⌕</span><input id="bb-q" type="search" placeholder="Search recipes, platforms…" data-ph-en="Search recipes, platforms…" data-ph-ja="レシピ・プラットフォームで検索…" aria-label="Search build assets" autocomplete="off"></label>'
        + sel("bb-platform", "Platform", popts) + sel("bb-type", "Type", topts) + sel("bb-status", "Test status", sopts)
        + f'<button class="text-button" id="bb-reset" type="button">{both(T("Reset filters", "絞り込み解除"))}</button></div>'
        f'<div class="cards bb-cards" id="bb-cards">{cards}</div><p class="empty" id="bb-empty" hidden>{both(T("No exact matches. Reset the filters.", "一致する項目がありません。絞り込みを解除してください。"))}</p></section>'
        f'<section class="container bb-section" id="compat"><h2>{both(T("Platform compatibility", "プラットフォームの対応状況"))}</h2>'
        f'{both(T("Status is about the current BSV starter for each platform, not the platform itself. Never read it as Verified.", "状態は各プラットフォーム向けのBSVスターターの現状であり、プラットフォーム自体の評価ではありません。検証済みという意味ではありません。"), "p", "small")}'
        f'<div class="bb-table-wrap"><table class="qa-table"><thead><tr><th>Platform</th><th>Extensibility path</th><th>Current BSV asset</th><th>Status</th></tr></thead><tbody>{crow}</tbody></table></div></section>'
    )
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "name": "Build your own chart tool — BotShelf Vampire Traders Library", "url": ORIGIN + "/trading/build/",
                         "isPartOf": {"@type": "CollectionPage", "name": "Traders Library", "url": ORIGIN + "/trading/"}}, ensure_ascii=False)
    write(site / "trading/build/index.html", trader_shell(site, "Build your own chart tool — Traders Library · BotShelf Vampire",
          "Original recipes, blocks and a code generator for TradingView, MT5, MT4, cTrader (C# / Python), Bookmap, NinjaTrader, Quantower, Sierra Chart, GoCharting, ProRealTime, MotiveWave, Vela, JForex, TradeStation, ATAS, AmiBroker, thinkorswim, Tradovate, backtrader, Backtesting.py and NautilusTrader. Honest test status.",
          "/trading/build/", hub, extra_head=f'<script type="application/ld+json">{jsonld}</script>'))
    meta = [{k: r[k] for k in ("id", "slug", "title", "platforms", "type", "status", "featured", "summary")} | {"url": ("/trading/build/#path" if r["id"] == "trader-build-own-chart" else f"/trading/tools/{r['slug']}.html"), "source_gated": r["gated"]} for r in allr]
    write(site / "trading/build/toolkit.v1.json", json.dumps({"schema": "bsv-trader-build/v1", "source": "BotShelfVampire/botshelf trader-toolkit/catalog.json", "entries": meta}, ensure_ascii=False, indent=1) + "\n")

    # ---- entry point inside the EXISTING Traders Library page
    idx_p = site / "trading/index.html"
    idx = idx_p.read_text()
    chip = f'<a href="/trading/build/" class="chip bb-entry-chip">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a>'
    idx = replace_block(idx, "trader-chip", chip, '<a href="guides/choose.html" class="chip" data-guide="choose">')
    strip = (f'<section class="container bb-entry" aria-label="Build your own chart tool"><div><div class="eyebrow">{both(T("NEW · BUILD", "新着・作る"))}</div>'
             f'<h2>{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</h2>'
             f'{both(T(f"{len(recipes)} recipes, a Pine/MQL5/MQL4/cTrader/Bookmap/NinjaTrader/Quantower/Sierra Chart/ProRealTime/GoCharting/MotiveWave/Vela/JForex/TradeStation/ATAS/AmiBroker/thinkorswim/Tradovate/backtrader/Backtesting.py/NautilusTrader generator and starters for {len(platforms)} platforms — including Vela for your own web chart and OpenMarkets as a data/agent input. Original BSV source; nothing runtime-tested yet.", f"レシピ{len(recipes)}本、Pine・MQL5・MQL4・cTrader・Bookmap・NinjaTrader・Quantower向けのコード生成、{len(platforms)}のプラットフォーム向けスターター。自作Webチャート用のVela、データ・エージェント連携のOpenMarketsも。BSVオリジナルのソースで、実行検証はまだです。"), "p")}</div>'
             f'<a class="btn primary" href="/trading/build/">{both(T("Start building →", "作り始める →"))}</a></section>')
    idx = replace_block(idx, "trader-strip", strip, '<div class="container main-layout" id="collection">')
    idx = re.sub(r'<link rel="stylesheet" href="/trading/assets/build\.[^"]+\.css">', "", idx)
    idx = idx.replace("</head>", f'<link rel="stylesheet" href="{ASSET["tcss"]}"></head>', 1)
    idx_p.write_text(idx, encoding="utf-8")
    return {"trader_assets": len(allr), "recipes": len(recipes), "platforms": platforms, "public_pages": [f"/trading/tools/{r['slug']}.html" for r in allr if r["id"] != "trader-build-own-chart"] + ["/trading/build/"]}


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
def lib_shell(site: Path, title: str, desc: str, canonical: str, body: str, robots: str = "index,follow", extra_head: str = "") -> str:
    li = (site / "library/index.html").read_text()
    hdr = li[li.find("<header"): li.find("</header>") + 9]
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">\n<link rel="canonical" href="{ORIGIN}{canonical}">\n<meta name="robots" content="{robots}">\n'
        '<link rel="icon" href="/img/mark.jpg" type="image/jpeg">\n<link rel="stylesheet" href="/css/shelf.css">\n'
        f'<link rel="stylesheet" href="{ASSET["acss"]}">\n{extra_head}</head>\n<body class="bsv-ai-toolkit">\n' + hdr +
        f'\n<main class="wrap">{body}</main>\n<footer><p>Original BSV templates and starters (MIT). BSV does not host or control the external products named here; their names belong to their owners.</p>'
        '<p data-lang-show="ja" hidden>BSVオリジナルのテンプレートとスターター（MITライセンス）。ここに名前のある外部サービスをBSVが運営・管理しているわけではありません。名称は各社のものです。</p>'
        '<p class="muted">No secrets in templates. No destructive commands. No auto-spend.</p></footer>\n'
        f'<script src="/js/i18n.js" defer></script>\n<script src="/js/nav-mobile.js" defer></script>\n<script src="{ASSET["ajs"]}" defer></script>\n</body>\n</html>\n'
    )


def ai_records(repo: Path, copy: dict) -> list[dict]:
    cat = json.loads((repo / "ai-toolkit/catalog.json").read_text())
    out = []
    for e in cat["entries"]:
        c = copy["ai"].get(e["id"]) or {"job": "local-worker", "summary": T(e["title"], e["title"])}  # add real copy in toolkit-site-copy.json
        files = files_for(repo, e["path"])
        pdir = (repo / e["path"]) if (repo / e["path"]).is_dir() else (repo / e["path"]).parent
        readme = (pdir / "README.md") if (pdir / "README.md").exists() else None
        if readme and readme not in files:
            files = files + [readme]
        refs = set()
        for f in files:
            refs |= set(re.findall(r"https?://[^\s)<>`\"]+", f.read_text()))
        out.append({"id": e["id"], "title": e["title"], "framework": e["platform"], "path": e["path"], "type": e["type"], "status": e["status"], "featured": bool(e.get("featured")),
                    "job": c["job"], "summary": c["summary"], "files": files, "base": pdir, "refs": sorted(u.rstrip(".,") for u in refs if not re.search(r"example|localhost|127\.0\.0\.1|0\.0\.0\.0|host\.docker\.internal|:\d{2,5}(/|$)|botshelfvampire\.com", u))})
    return out


def build_ai(site: Path, repo: Path, copy: dict) -> dict:
    recs = ai_records(repo, copy)
    # handoff-packet checker: served from /library/source/ (behind the free email gate), used only on that packet's source page
    for old in (site / "library/source").glob("handoff-check.*.js"):
        old.unlink()
    hjs = (repo / "scripts/site/handoff_check.js").read_text()
    hname = f"library/source/handoff-check.{hashlib.sha256(hjs.encode()).hexdigest()[:8]}.js"
    write(site / hname, hjs)
    hmd = (repo / "ai-toolkit/common/ai-team-handoff-packet.md").read_text()
    ho_tpl = re.search(r"```text\n(.*?)```", hmd, re.S).group(1)
    ho_opts = "".join(f'<option value="{esc(x["id"])}" data-path="{esc(x["path"])}" data-fw="{esc(x["framework"])}" data-st="{esc(x["status"])}">{esc(x["title"])}</option>' for x in recs)
    checker = ('<section class="section" id="ho-checker"><p class="section-label">Check a filled packet</p>'
               + lib_both(T("Paste a filled packet and press Check. It applies the packet's own rules (every section present, one status, DONE only with evidence, owner approval YES or NO, one next action, no guessed results). It runs in this browser only: nothing is uploaded or stored. It checks structure and wording, not whether the facts are true.",
                            "記入した packet を貼り付けて「Check」を押します。packet 自身のルール（すべての項目があること、status は1つ、DONE は根拠があるときだけ、owner approval は YES か NO、次の一手は1つ、推測で結果を書かない）で確かめます。このブラウザの中だけで動き、何もアップロード・保存しません。確かめるのは形と書き方で、内容が正しいかどうかではありません。"), "p", "muted")
               + f'<p><label for="ho-item">Start from a toolkit item (optional)</label></p><p><select id="ho-item"><option value="">Choose…</option>{ho_opts}</select> '
               f'<button type="button" class="btn" id="ho-start" data-ho-tpl="{esc(ho_tpl)}">Start a packet</button></p>'
               + lib_both(T("Fills only what the catalog states (job id, NOT_STARTED, the source path, the framework, the catalog status as a limitation) into an empty box. Everything else stays blank for you, including owner approval.", "カタログに書かれていること（job id、NOT_STARTED、ソースの場所、フレームワーク、カタログの状態を limitations に）だけを、空の入力欄に入れます。owner approval を含め、ほかは空のままです。"), "p", "muted")
               + '<p><label for="ho-text">Filled packet</label></p><p><textarea id="ho-text" rows="14" cols="80" spellcheck="false"></textarea></p>'
               '<p><button type="button" class="btn" id="ho-check">Check</button></p><div id="ho-out" aria-live="polite"></div></section>')
    lic = (repo / "LICENSE").read_bytes()
    st = copy["status"]
    for r in recs:
        copy["ai_frameworks"].setdefault(r["framework"], {"slug": re.sub(r"[^a-z0-9]+", "-", r["framework"].lower()).strip("-"), "en": r["framework"], "ja": r["framework"], "refs": []})
    fw_order = list(copy["ai_frameworks"].keys())
    jobs = copy["ai_jobs"]

    def related(r):
        # related items (AI toolkit improvement, 2026-10-04): same job on other frameworks, then other items for the same
        # framework; catalog facts only (title, framework, status), public summary pages only
        sj = [x for x in recs if x["id"] != r["id"] and x["job"] == r["job"]]
        sf = [x for x in recs if x["id"] != r["id"] and x["framework"] == r["framework"] and x not in sj]
        li = lambda x: f'<li><a data-tk-rel="{esc(x["id"])}" href="/library/toolkit/{x["id"]}/">{esc(x["title"])}</a> — <span class="muted">{esc(x["framework"])} · {esc(st[x["status"]]["en"])}</span></li>'
        out = ""
        if sj:
            out += f'<p class="section-label">Same job, other frameworks<span data-lang-show="ja" hidden> · 同じ仕事・ほかのフレームワーク</span></p><ul class="tk-list">' + "".join(li(x) for x in sj) + "</ul>"
        if sf:
            out += f'<p class="section-label">More for {esc(r["framework"])}<span data-lang-show="ja" hidden> · {esc(r["framework"])} のほかの項目</span></p><ul class="tk-list">' + "".join(li(x) for x in sf) + "</ul>"
        return f'<section class="section" id="tk-related">{out}</section>' if out else ""

    for r in recs:
        # gated source
        blocks, zentries = [], []
        for i, f in enumerate(r["files"]):
            code = f.read_text()
            name = str(f.relative_to(r["base"]))
            cid = f"src-{r['id']}-{i}"
            blocks.append(f'<details class="lib-src" {"open" if i == 0 else ""}><summary><code>{esc(name)}</code> · {len(code.encode())} bytes</summary>'
                          f'<p><button type="button" class="btn" data-tk-copy="{cid}">Copy</button></p><pre id="{cid}" tabindex="0"><code>{esc(code)}</code></pre>'
                          f'<p class="muted">SHA256 {hashlib.sha256(code.encode()).hexdigest()}</p></details>')
            zentries.append((f"bsv-{r['id']}/{name}", code.encode()))
        zentries.append((f"bsv-{r['id']}/LICENSE.txt", lic))
        write(site / f"library/source/{r['id']}.zip", det_zip(zentries), binary=True)
        body = (f'<p class="kicker"><a href="/library/">Library</a> · <a href="/library/toolkit/">AI toolkits</a> · {esc(r["framework"])}</p><h1>{esc(r["title"])}</h1>'
                f'{lib_both(r["summary"], "p", "catch")}<p class="lib-meta"><span class="tk-badge">{esc(r["framework"])}</span><span class="tk-badge tk-warn">{esc(st[r["status"]]["en"])}</span><span class="tk-badge">ORIGINAL · MIT</span></p>'
                f'<p><a class="btn-fat btn-solid" href="/library/source/{r["id"]}.zip">Download ZIP (source + LICENSE)</a></p>' + "".join(blocks)
                + (checker if r["id"] == "ai-team-handoff" else "")
                + f'<details class="lib-src"><summary>License (MIT)</summary><pre>{esc(lic.decode())}</pre></details><p><a href="/library/toolkit/{r["id"]}/">← Summary page</a></p>')
        sh = lib_shell(site, f"{r['title']} — source | BotShelf Vampire", r["summary"]["en"], f"/library/toolkit/{r['id']}/", body, robots="noindex,nofollow")
        if r["id"] == "ai-team-handoff":
            sh = sh.replace("</body>", f'<script src="/{hname}" defer></script>\n</body>', 1)
        write(site / f"library/source/{r['id']}.html", sh)
        # public detail
        fw = copy["ai_frameworks"].setdefault(r["framework"], {"slug": re.sub(r"[^a-z0-9]+", "-", r["framework"].lower()).strip("-"), "en": r["framework"], "ja": r["framework"], "refs": []})
        names = "".join(f'<li><code>{esc(f.relative_to(r["base"]))}</code> · {f.stat().st_size} bytes</li>' for f in r["files"])
        refs = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(u)}</a></li>' for u in r["refs"])
        nxt = f"/library/source/{r['id']}.html"
        body = (f'<p class="kicker"><a href="/library/">Library</a> · <a href="/library/toolkit/">AI toolkits</a> · <a href="/library/toolkit/#fw-{fw["slug"]}">{esc(r["framework"])}</a></p>'
                f'<h1>{esc(r["title"])}</h1>{lib_both(r["summary"], "p", "catch")}'
                f'<p class="lib-meta"><span class="tk-badge">{esc(r["framework"])}</span><span class="tk-badge">{esc(jobs[r["job"]]["en"])}</span><span class="tk-badge">{esc(copy["ai_types"][r["type"]]["en"])}</span><span class="tk-badge tk-warn">{esc(st[r["status"]]["en"])}</span><span class="tk-badge">ORIGINAL · MIT</span></p>'
                f'<section class="section"><p class="section-label">Open the template</p>'
                f'<p><a class="btn-fat btn-solid" href="{nxt}" data-tk-gated>Open source — free email verification</a></p>'
                f'{lib_both(T("Summaries are public. Viewing, copying and downloading BSV-provided source requires free email verification. If you are sent to registration, verify your email and then press this button again.", "解説は登録なしで読めます。BSVが提供するコードの閲覧・コピー・ダウンロードには無料のメール確認が必要です。登録画面に移動した場合は、メール確認を済ませてからもう一度このボタンを押してください。"), "p", "muted")}</section>'
                f'<section class="section"><p class="section-label">About {esc(r["framework"])}</p>{lib_both(T(fw["en"], fw["ja"]), "p")}</section>'
                f'<section class="section"><p class="section-label">Test status</p><p>{esc(st[r["status"]]["en"])}. BSV has not run this on a user account or runtime; file presence and CI syntax checks are not runtime verification.</p>'
                f'<p data-lang-show="ja" hidden>{esc(st[r["status"]]["ja"])}。BSVではユーザーのアカウントや実行環境で動かしていません。ファイルがあること、CIの構文確認は実行検証ではありません。</p></section>'
                f'<section class="section"><p class="section-label">Files</p><ul>{names}</ul></section>'
                + (f'<section class="section"><p class="section-label">Official references</p><ul>{refs}</ul></section>' if refs else "")
                + related(r)
                + f'<section class="section"><p class="section-label">Need it for another framework?</p>{lib_both(T("Ask for a version for the framework or runtime you use. The request form opens with this item named; nothing is sent until you press send with a verified email.", "使っているフレームワークや実行環境向けの版をリクエストできます。フォームにはこの項目名が入った状態で開きます。メール確認済みで送信ボタンを押すまで何も送られません。"), "p", "muted")}'
                  f'<p><a class="btn-fat" data-tk-ask="{esc(r["id"])}" href="/requests/?area=ai-workflows&amp;toolkit={esc(r["id"])}#rq-form">Ask for another framework →</a></p></section>')
        # CreativeWork JSON-LD (#8 tranche 14): catalog facts only (no rating, no review, no test claim)
        ld = {"@context": "https://schema.org", "@type": "CreativeWork", "name": r["title"], "description": r["summary"]["en"], "url": f"{ORIGIN}/library/toolkit/{r['id']}/",
              "license": "https://spdx.org/licenses/MIT.html", "isAccessibleForFree": True, "inLanguage": "en", "genre": copy["ai_types"][r["type"]]["en"], "about": r["framework"],
              "creator": {"@type": "Organization", "name": "BotShelf Vampire", "url": ORIGIN + "/"}, "isPartOf": {"@type": "CollectionPage", "url": ORIGIN + "/library/toolkit/"}}
        write(site / f"library/toolkit/{r['id']}/index.html", lib_shell(site, f"{r['title']} — {r['framework']} | AI toolkits | BotShelf Vampire", r["summary"]["en"], f"/library/toolkit/{r['id']}/", body,
                                                                    extra_head='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>\n"))

    def card(r):
        s = " ".join([r["title"], r["framework"], r["job"], r["summary"]["en"], r["summary"]["ja"]]).lower()
        return (f'<article class="tk-card" data-framework="{esc(r["framework"])}" data-job="{esc(r["job"])}" data-status="{esc(r["status"])}" data-search="{esc(s)}">'
                f'<p class="muted tk-fw">{esc(r["framework"])} · {esc(copy["ai_types"][r["type"]]["en"])}</p><h3><a href="/library/toolkit/{r["id"]}/">{esc(r["title"])}</a></h3>'
                f'{lib_both(r["summary"], "p")}<p class="lib-meta"><span class="tk-badge tk-warn">{esc(st[r["status"]]["en"])}</span><span class="tk-badge">{esc(jobs[r["job"]]["en"])}</span></p></article>')

    by_job = "".join(f'<section class="section" id="job-{j}"><p class="section-label">{esc(jobs[j]["en"])}<span data-lang-show="ja" hidden> · {esc(jobs[j]["ja"])}</span></p><div class="tk-grid">' + "".join(card(r) for r in recs if r["job"] == j) + "</div></section>" for j in jobs if any(r["job"] == j for r in recs))
    by_fw = "".join(f'<section class="section" id="fw-{copy["ai_frameworks"][f]["slug"]}"><p class="section-label">{esc(f)}</p>{lib_both(T(copy["ai_frameworks"][f]["en"], copy["ai_frameworks"][f]["ja"]), "p", "muted")}<ul class="tk-list">' + "".join(f'<li><a href="/library/toolkit/{r["id"]}/">{esc(r["title"])}</a> — <span class="muted">{esc(st[r["status"]]["en"])}</span></li>' for r in recs if r["framework"] == f) + "</ul></section>" for f in fw_order if any(r["framework"] == f for r in recs))
    existing = [("ollama", "Ollama"), ("lm-studio", "LM Studio"), ("open-webui", "Open WebUI"), ("n8n", "n8n"), ("crewai", "CrewAI"), ("langgraph", "LangGraph"), ("mcp", "MCP")]
    ex = "".join(f'<a class="lib-chip" href="/library/{s}/">{n}</a>' for s, n in existing)
    fchips = "".join(f'<a class="lib-chip" href="#fw-{copy["ai_frameworks"][f]["slug"]}">{esc(f)} ({sum(1 for r in recs if r["framework"] == f)})</a>' for f in fw_order)
    jchips = "".join(f'<a class="lib-chip" href="#job-{j}">{esc(jobs[j]["en"])}</a>' for j in jobs if any(r["job"] == j for r in recs))
    fopt = "".join(f'<option value="{esc(f)}">{esc(f)}</option>' for f in fw_order)
    jopt = "".join(f'<option value="{esc(j)}">{esc(jobs[j]["en"])}</option>' for j in jobs)
    sopt = "".join(f'<option value="{s}">{esc(st[s]["en"])}</option>' for s in sorted({r["status"] for r in recs}))
    hub = (f'<p class="kicker">BUILD LIBRARY · AI TOOLKITS</p><h1>Agent toolkits — by job, then by framework.</h1>'
           f'{lib_both(T("Original templates and starters for OpenAI Dots, Hugging Face (MCP, Spaces, Skills, Tiny Agents), LM Studio Bionic, smolagents, Letta and the OpenAI Agents SDK, plus LangGraph and CrewAI runners for each Library AI Team task. Part of the existing Build Library — the Ollama, LM Studio, Open WebUI, n8n, CrewAI, LangGraph and MCP recipes stay where they are.", "OpenAI Dots、Hugging Face（MCP・Spaces・Skills・Tiny Agents）、LM Studio Bionic、smolagents、Letta、OpenAI Agents SDK向けのオリジナルのテンプレートとスターターに加え、Library AI Teamの仕事ごとに動かすLangGraph・CrewAIのランナーもあります。既存のBuild Libraryの一部で、Ollama・LM Studio・Open WebUI・n8n・CrewAI・LangGraph・MCPのレシピはそのまま使えます。"), "p", "catch")}'
           f'<p class="what"><strong>{len(recs)} toolkit items</strong> · <strong>{len(fw_order)}</strong> frameworks · <strong>Runtime-verified by BSV: 0</strong> (every item shows its real status).</p>'
           f'{lib_both(T("Summaries are public. Opening, copying or downloading the templates requires free email verification. Free stays free.", "解説は登録なしで読めます。テンプレートの閲覧・コピー・ダウンロードには無料のメール確認が必要です。無料のものは無料のままです。"), "p", "muted")}'
           f'<p class="section-label">Browse by job</p><div class="lib-chip-row">{jchips}</div>'
           f'<p class="section-label">Browse by framework</p><div class="lib-chip-row">{fchips}</div>'
           f'<p class="section-label">Existing Library platforms</p><div class="lib-chip-row">{ex}</div>'
           f'<div class="lib-filters tk-filters" aria-label="Toolkit filters"><div class="row"><label for="tk-q">Search</label><input id="tk-q" type="search" placeholder="Filter: memory, MCP, local, guardrails…" autocomplete="off"><span class="muted" id="tk-count"></span></div>'
           f'<div class="row"><label for="tk-f-framework">Framework</label><select id="tk-f-framework"><option value="">Any</option>{fopt}</select><label for="tk-f-job">Job</label><select id="tk-f-job"><option value="">Any</option>{jopt}</select><label for="tk-f-status">Status</label><select id="tk-f-status"><option value="">Any</option>{sopt}</select></div></div>'
           f'{by_job}<section class="section"><p class="section-label">By framework / runtime</p></section>{by_fw}'
           + '<section class="section" id="tk-matrix"><p class="section-label">Jobs covered, by framework<span data-lang-show="ja" hidden> · フレームワークごとの対応する仕事</span></p><ul class="tk-list">'
           + "".join(f'<li data-tk-fw="{esc(f)}"><strong><a data-tk-fw-link href="?framework={esc(urllib.parse.quote(f))}#tk-q">{esc(f)}</a></strong> — ' + ", ".join(f'<a href="#job-{j}">{esc(jobs[j]["en"])}</a> ({sum(1 for r in recs if r["framework"] == f and r["job"] == j)})' for j in jobs if any(r["framework"] == f and r["job"] == j for r in recs)) + '</li>' for f in fw_order if any(r["framework"] == f for r in recs))
           + '</ul>' + lib_both(T("Counted from the catalog: which jobs each framework has BSV items for. Not a ranking and not a test result.", "カタログから数えた、フレームワークごとにBSVの項目がある仕事です。順位でも検証結果でもありません。"), "p", "muted") + '</section>'
           f'<section class="section" id="tk-ask"><p class="section-label">Not listed?</p>{lib_both(T("Ask for a framework, runtime or tool that is not here. Requests are reviewed before anything is listed; nothing is sent until you press send with a verified email.", "ここにないフレームワーク・実行環境・ツールをリクエストできます。掲載の前に確認します。メール確認済みで送信ボタンを押すまで何も送られません。"), "p", "muted")}'
           '<p><a class="btn-fat" data-tk-ask-hub href="/requests/?area=ai-workflows#rq-form">Ask for a framework or tool →</a></p></section>'
           f'<section class="section how-box"><p class="section-label">How these differ</p><p>Bionic is an agent app/harness for open models; smolagents is a lightweight Python framework; Letta focuses on persistent state and memory; the OpenAI Agents SDK provides orchestration primitives (tools, handoffs, guardrails, sessions); Dots are always-on responsibilities inside OpenAI\'s product; Hugging Face provides MCP, Spaces, Skills and Tiny Agents; the LangGraph and CrewAI team runners run one Library AI Team task at a time with your approval before saving. Choose by job — they are not interchangeable.</p></section>')
    write(site / "library/toolkit/index.html", lib_shell(site, "AI agent toolkits — Dots, Hugging Face, Bionic, smolagents, Letta, OpenAI Agents SDK, LangGraph, CrewAI | Build Library | BotShelf Vampire",
          "Original BSV templates and starters for OpenAI Dots, Hugging Face MCP/Spaces/Skills/Tiny Agents, LM Studio Bionic, smolagents, Letta, the OpenAI Agents SDK, and LangGraph/CrewAI team runners — organised by job and framework, with honest test status.", "/library/toolkit/", hub))
    meta = [{"id": r["id"], "title": r["title"], "framework": r["framework"], "job": r["job"], "type": r["type"], "status": r["status"], "summary": r["summary"], "url": f"/library/toolkit/{r['id']}/", "source_gated": True,
             "sourceAccess": "free email verification", "license": "MIT", "runtimeTestedByBSV": False, "capabilityId": "bsv.ai-toolkit." + r["id"]} for r in recs]
    write(site / "library/toolkit/toolkit.v1.json", json.dumps({"schema": "bsv-ai-toolkit/v1", "source": "BotShelfVampire/botshelf ai-toolkit/catalog.json", "counts": {"entries": len(meta), "frameworks": len({m["framework"] for m in meta}), "runtimeTestedByBSV": 0}, "entries": meta}, ensure_ascii=False, indent=1) + "\n")

    # entry inside EXISTING library index
    lp = site / "library/index.html"
    li = lp.read_text()
    chips = "".join(f'<a class="lib-chip" href="/library/toolkit/#fw-{copy["ai_frameworks"][f]["slug"]}">{esc(f)} ({sum(1 for r in recs if r["framework"] == f)})</a>' for f in fw_order)
    block = (f'<p class="section-label">Agent toolkits (new)</p><div class="lib-chip-row"><a class="lib-chip" href="/library/toolkit/"><strong>All AI toolkits ({len(recs)})</strong></a>{chips}</div>'
             f'<p class="muted" data-lang-show="en">Dots, Hugging Face, Bionic, smolagents, Letta, OpenAI Agents SDK, LangGraph and CrewAI templates — organised by job. Source opens after free email verification; status shown honestly.</p>'
             f'<p class="muted" data-lang-show="ja" hidden>Dots・Hugging Face・Bionic・smolagents・Letta・OpenAI Agents SDK・LangGraph・CrewAIのテンプレートを仕事別に整理。コードは無料のメール確認後に開けます。検証状態はそのまま表示しています。</p>')
    block = '<section class="tk-entry" aria-label="AI agent toolkits">' + block + '<p><a class="tk-entry-btn" href="/library/toolkit/">Open AI toolkits →</a></p></section>'
    li = replace_block(li, "ai-chips", block, '<div class="lib-filters" aria-label="Library filters">')
    li = re.sub(r'<link rel="stylesheet" href="/library/toolkit/toolkit\.[^"]+\.css">\n?', "", li)
    li = li.replace("</head>", f'<link rel="stylesheet" href="{ASSET["acss"]}">\n</head>', 1)
    lp.write_text(li, encoding="utf-8")

    # gate: add /library/source/* to the existing fail-closed edge gate
    gp = site / "netlify/edge-functions/free-session-gate.ts"
    gp = gp if gp.exists() else site.parent / "netlify/edge-functions/free-session-gate.ts"
    g = gp.read_text()
    if GATE_PATH not in g:
        g2 = g.replace('"/trading/downloads/*"]', f'"/trading/downloads/*", "{GATE_PATH}"]', 1)
        if g2 == g:
            raise SystemExit("could not add gate path")
        gp.write_text(g2, encoding="utf-8")
    return {"ai_items": len(recs), "public_pages": ["/library/toolkit/"] + [f"/library/toolkit/{r['id']}/" for r in recs]}


def assets(site: Path):
    css = """
.bsv-build .bb-hero h1{font-size:clamp(2rem,6vw,3.4rem)}
.bb-section{margin:2.2rem auto}
.bb-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:0;list-style:none;counter-reset:s}
.bb-steps li{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;counter-increment:s}
.bb-steps li strong::before{content:counter(s) ". ";color:var(--green)}
.bb-steps li p{color:var(--muted);margin:.4rem 0 0;font-size:.92rem}
.bb-paths{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.bb-path{display:flex;flex-direction:column;gap:6px;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px;text-decoration:none;color:var(--text)}
.bb-path:hover,.bb-path:focus{border-color:var(--green)}
.bb-path small{color:var(--green);letter-spacing:.06em}
.bb-path span{color:var(--muted);font-size:.9rem}
.bb-filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bb-filters .search-wrap{flex:1 1 240px}
.bb-sel select{min-height:40px}
.bb-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.bb-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:6px}
.bb-card h3{margin:0;font-size:1.05rem}.bb-card p{margin:0;color:var(--muted);font-size:.92rem}
.bb-meta{display:flex;justify-content:space-between;color:var(--muted);font-size:.8rem;gap:8px}
.bb-flag{color:var(--green);font-weight:600}
.bb-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:auto}
.bb-tags>span,.bb-status,.bb-orig{border:1px solid var(--line);border-radius:999px;padding:2px 8px;font-size:.75rem}
.bb-warn{color:var(--danger);border-color:var(--danger)!important}.bb-ok{color:var(--green);border-color:var(--green)!important}
.bb-orig{color:var(--green)}
.bb-callout{border-left:3px solid var(--green);padding:8px 12px;background:var(--panel2)}
.bb-table-wrap{overflow-x:auto}.bb-table-wrap table{min-width:640px}
.bb-entry{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;border:1px solid var(--green);border-radius:14px;padding:16px 18px;margin-top:14px;margin-bottom:14px;background:var(--panel)}
.bb-entry h2{margin:.2rem 0}.bb-entry p{margin:0;color:var(--muted);max-width:760px}
.bb-entry-chip{border-color:var(--green)!important;color:var(--green)!important}
.bsv-build .sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.bsv-build pre{white-space:pre;overflow-x:auto;max-width:100%}
.bsv-build .btn.primary,.bb-entry .btn.primary{background:var(--green);border-color:var(--green);color:#0d100f}
.bsv-build .hero-stats b,.bsv-build .stat-total strong,.bsv-build .eyebrow,.bb-entry .eyebrow{color:var(--green)!important}
.bsv-build .hero-stats{border-top-color:var(--line)!important}
@media (max-width:640px){.bb-filters select,.bb-filters .search-wrap{width:100%}.bb-sel{width:100%}.bb-entry .btn{width:100%;text-align:center}}
"""
    js = r"""(()=>{'use strict';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const read=k=>{try{return localStorage.getItem(k)}catch{return null}},store=(k,v)=>{try{localStorage.setItem(k,v)}catch{}};
let lang='en';
function setLang(v){lang=v==='ja'?'ja':'en';document.documentElement.lang=lang;store('bsv-traders-lang',lang);
$$('[data-set-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.setLang===lang)));
$$('option[data-en]').forEach(o=>o.textContent=o.dataset[lang]);
const q=$('#bb-q');if(q)q.placeholder=q.dataset['ph'+(lang==='ja'?'Ja':'En')];
$$('a[data-source-access]').forEach(a=>{const u=new URL(a.href,location.origin);u.searchParams.set('lang',lang);a.href=u.pathname+u.search});}
$$('[data-set-lang]').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.setLang)));
let p=null;try{p=new URL(location.href).searchParams.get('lang')}catch{}
setLang(p||read('bsv-traders-lang')||read('bot-shelf-lang')||((navigator.language||'').startsWith('ja')?'ja':'en'));
const cards=$$('.bb-card');
function filter(){if(!cards.length)return;const q=($('#bb-q')?.value||'').toLowerCase().trim(),pl=$('#bb-platform')?.value||'',ty=$('#bb-type')?.value||'',st=$('#bb-status')?.value||'';let n=0;
cards.forEach(c=>{const ok=(!q||c.dataset.search.includes(q))&&(!pl||c.dataset.platforms.split('|').includes(pl))&&(!ty||c.dataset.type===ty)&&(!st||c.dataset.status===st);c.hidden=!ok;if(ok)n++});
const cnt=$('#bb-count');if(cnt)cnt.textContent=n;const e=$('#bb-empty');if(e)e.hidden=n>0;}
['#bb-q','#bb-platform','#bb-type','#bb-status'].forEach(s=>{const el=$(s);if(el){el.addEventListener('input',filter);el.addEventListener('change',filter)}});
const r=$('#bb-reset');if(r)r.addEventListener('click',()=>{['#bb-q','#bb-platform','#bb-type','#bb-status'].forEach(s=>{const el=$(s);if(el)el.value=''});filter()});
const params=new URL(location.href).searchParams;['platform','type','status'].forEach(k=>{const v=params.get(k),el=$('#bb-'+k);if(v&&el)el.value=v});filter();
function toast(t){const el=$('#toast');if(!el)return;el.textContent=t;el.hidden=false;setTimeout(()=>el.hidden=true,1600)}
$$('[data-bb-copy]').forEach(b=>b.addEventListener('click',()=>{const el=document.getElementById(b.dataset.bbCopy);if(!el||!navigator.clipboard)return;navigator.clipboard.writeText(el.innerText).then(()=>toast(lang==='ja'?'コピーしました':'Copied'))}));
})();
"""
    tk_css = """
.tk-entry{border:1px solid #bad4b7;border-radius:14px;padding:14px 16px;margin:16px 0 20px}
.tk-entry .section-label{color:#bad4b7}
.tk-entry .lib-chip-row{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 10px}
.tk-entry .lib-chip{display:inline-block;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:5px 11px;font-size:.85rem;text-decoration:none;color:#e8ece6}
.tk-entry .tk-entry-btn{display:inline-block;background:#bad4b7;color:#0d100f;border-radius:999px;padding:8px 16px;text-decoration:none;font-weight:600}
.bsv-ai-toolkit .tk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.bsv-ai-toolkit .tk-card{border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:14px}
.bsv-ai-toolkit .tk-card h3{margin:.2rem 0 .4rem;font-size:1.05rem}
.bsv-ai-toolkit .tk-fw{font-size:.8rem;margin:0}
.bsv-ai-toolkit .tk-badge{display:inline-block;border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:2px 9px;font-size:.78rem;margin:0 6px 6px 0}
.bsv-ai-toolkit .tk-warn{border-color:#e9b99e;color:#e9b99e}
.bsv-ai-toolkit .tk-list li{margin:.3rem 0}
.bsv-ai-toolkit pre{white-space:pre;overflow-x:auto;max-width:100%}
.bsv-ai-toolkit .lib-filters select,.bsv-ai-toolkit .lib-filters input{max-width:100%}
.bsv-ai-toolkit .lib-chip-row,.lib-chip-row.tk-row{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px}
.bsv-ai-toolkit .lib-chip{display:inline-block;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:5px 11px;font-size:.85rem;text-decoration:none;color:#e8ece6}
.bsv-ai-toolkit .lib-chip:hover,.bsv-ai-toolkit .lib-chip:focus{border-color:#bad4b7;color:#bad4b7}
.bsv-ai-toolkit main a:not(.lib-chip):not(.btn-fat){color:#bad4b7}
.bsv-ai-toolkit .kicker,.bsv-ai-toolkit .section-label{color:#bad4b7}
.bsv-ai-toolkit .btn-fat.btn-solid{background:#bad4b7;border-color:#bad4b7;color:#0d100f}
@media (max-width:640px){.bsv-ai-toolkit .lib-filters .row{display:flex;flex-direction:column;align-items:stretch;gap:6px}}
"""
    tk_js = r"""(function(){
var cards=[].slice.call(document.querySelectorAll('.tk-card'));
var q=document.getElementById('tk-q'),cnt=document.getElementById('tk-count');
var sels=['framework','job','status'].map(function(k){return document.getElementById('tk-f-'+k)});
function apply(){if(!cards.length)return;var t=(q&&q.value||'').toLowerCase().trim(),n=0;
cards.forEach(function(c){var ok=!t||c.getAttribute('data-search').indexOf(t)>-1;
sels.forEach(function(s){if(s&&s.value&&c.getAttribute('data-'+s.id.replace('tk-f-',''))!==s.value)ok=false});
c.hidden=!ok;if(ok)n++});if(cnt)cnt.textContent=n+' shown';}
var keys=['framework','job','status'];
function fromUrl(){var u;try{u=new URL(location.href).searchParams}catch(e){return}
sels.forEach(function(s,i){var v=u.get(keys[i]);if(s&&v!==null&&[].some.call(s.options,function(o){return o.value===v}))s.value=v});
var t=u.get('q');if(q&&t!==null)q.value=t.slice(0,80);}
function toUrl(){if(!history.replaceState)return;var u;try{u=new URL(location.href)}catch(e){return}
sels.forEach(function(s,i){if(s&&s.value)u.searchParams.set(keys[i],s.value);else u.searchParams.delete(keys[i])});
var t=q&&q.value.trim();if(t)u.searchParams.set('q',t.slice(0,80));else u.searchParams.delete('q');
history.replaceState(null,'',u.pathname+u.search+u.hash);}
fromUrl();
if(q)q.addEventListener('input',function(){apply();toUrl()});sels.forEach(function(s){if(s)s.addEventListener('change',function(){apply();toUrl()})});apply();
[].forEach.call(document.querySelectorAll('[data-tk-copy]'),function(b){b.addEventListener('click',function(){var el=document.getElementById(b.getAttribute('data-tk-copy'));if(!el||!navigator.clipboard)return;navigator.clipboard.writeText(el.innerText).then(function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1600)})})});
})();
"""
    for key, rel, body in (("tcss", "trading/assets/build", css.strip() + "\n"), ("tjs", "trading/assets/build", js),
                           ("acss", "library/toolkit/toolkit", tk_css.strip() + "\n"), ("ajs", "library/toolkit/toolkit", tk_js)):
        ext = "css" if key.endswith("css") else "js"
        h = hashlib.sha256(body.encode()).hexdigest()[:8]
        name = f"{rel}.{VER}-{h}.{ext}"
        write(site / name, body)
        ASSET[key] = "/" + name


# ---------------------------------------------------------------------------
# Discovery: site search, sitemap, register return link
# ---------------------------------------------------------------------------
def build_discovery(site: Path, copy: dict) -> dict:
    tmeta = json.loads((site / "trading/build/toolkit.v1.json").read_text())["entries"]
    ameta = json.loads((site / "library/toolkit/toolkit.v1.json").read_text())["entries"]
    st = copy["status"]
    # site search: extend the index referenced by /search/
    sp = site / "search/index.html"
    sh = sp.read_text()
    m = re.search(r'/js/(bsv-search-page\.v[0-9a-z]+\.js)', sh)
    page_js = m.group(1)
    pj = (site / "js" / page_js).read_text()
    idx_name = re.search(r"(index\.v[0-9a-z]+\.json)", pj).group(1)
    if idx_name == f"index.{VER}.json":
        base = json.loads((site / "search" / idx_name).read_text())
    else:
        base = json.loads((site / "search" / idx_name).read_text())
    rows = [r for r in base["rows"] if not str(r.get("id", "")).startswith(("bsv-", "toolkit/"))]
    for e in tmeta:
        rows.append({"s": "trading", "id": e["slug"], "t": e["title"], "k": copy["trader_types"][e["type"]]["en"], "kj": copy["trader_types"][e["type"]]["ja"],
                     "c": "Build your own chart tool", "p": e["platforms"], "d": e["summary"]["en"], "dj": e["summary"]["ja"],
                     "x": f'ORIGINAL BSV MIT {st[e["status"]]["en"]} {st[e["status"]]["ja"]} recipe generator custom chart indicator dashboard scanner alert',
                     "u": e["url"], "uj": e["url"] + ("&lang=ja" if "?" in e["url"] else ("?lang=ja" if "#" not in e["url"] else "")), "a": "free"})
    for e in ameta:
        rows.append({"s": "build", "id": "toolkit/" + e["id"], "t": e["title"], "k": copy["ai_types"][e["type"]]["en"], "kj": copy["ai_types"][e["type"]]["ja"],
                     "c": copy["ai_jobs"][e["job"]]["en"], "p": [e["framework"]], "d": e["summary"]["en"], "dj": e["summary"]["ja"],
                     "x": f'AI agent toolkit ORIGINAL BSV MIT {st[e["status"]]["en"]} {copy["ai_jobs"][e["job"]]["ja"]}', "u": e["url"], "a": "free"})
    counts = {"trading": 0, "ai": 0, "build": 0}
    for r in rows:
        counts[r["s"]] = counts.get(r["s"], 0) + 1
    out = dict(base, counts=counts, rows=rows)
    new_idx = f"index.{VER}.json"
    write(site / "search" / new_idx, json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    new_js = f"bsv-search-page.{VER}.js"
    write(site / "js" / new_js, pj.replace(idx_name, new_idx))
    sp.write_text(sh.replace(f"/js/{page_js}", f"/js/{new_js}"), encoding="utf-8")
    # sitemap
    smp = site / "sitemap.xml"
    sm = smp.read_text()
    urls = ["/trading/build/"] + [e["url"] for e in tmeta if e["url"].startswith("/trading/tools/")] + ["/library/toolkit/"] + [e["url"] for e in ameta]
    add = "".join(f"<url><loc>{ORIGIN}{u}</loc><lastmod>2026-10-03</lastmod></url>" for u in urls if f"<loc>{ORIGIN}{u}</loc>" not in sm)
    if add:
        sm = sm.replace("</urlset>", add + "</urlset>")
        smp.write_text(sm, encoding="utf-8")
    # register: visible return link for AI toolkit source (no auto-redirect; the edge gate still decides)
    rp = site / "register.html"
    rh = rp.read_text()
    note = ('<p id="tk-next" class="muted" hidden data-tk-next>After you verify your email, '
            '<a id="tk-next-link" href="/library/toolkit/">open the AI toolkit template you chose</a>.'
            '<span data-lang-show="ja" hidden> メール確認が終わったら、<a id="tk-next-link-ja" href="/library/toolkit/">選んだAIツールキットのテンプレートを開いてください</a>。</span></p>'
            f'<script src="/library/toolkit/register-next.{VER}.js" defer></script>')
    rh = replace_block(rh, "register-next", note, '<main class="wrap">', before=False)
    rp.write_text(rh, encoding="utf-8")
    write(site / f"library/toolkit/register-next.{VER}.js",
          "(function(){var n=null;try{n=new URL(location.href).searchParams.get('next')}catch(e){}"
          "if(!n||!/^\\/library\\/source\\/[a-z0-9-]+\\.(html|zip)$/.test(n))return;"
          "var b=document.getElementById('tk-next');if(!b)return;"
          "['tk-next-link','tk-next-link-ja'].forEach(function(i){var a=document.getElementById(i);if(a)a.setAttribute('href',n)});b.hidden=false;})();\n")
    # robots.txt wording: owner is 「オーナー」
    rb = site / "robots.txt"
    if rb.exists() and "君" in rb.read_text():
        rb.write_text(rb.read_text().replace("君", "オーナー"), encoding="utf-8")
    return {"search_rows": len(rows), "counts": counts, "sitemap_added": add.count("<url>")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--only", choices=["trader", "ai", "all"], default="all")
    a = ap.parse_args()
    site, repo = Path(a.site), Path(a.repo)
    copy = json.loads((repo / "scripts/site/toolkit-site-copy.json").read_text())
    assets(site)
    rep = {}
    if a.only in ("trader", "all"):
        rep["trader"] = build_trader(site, repo, copy)
    if a.only in ("ai", "all"):
        rep["ai"] = build_ai(site, repo, copy)
    if a.only == "all":
        rep["discovery"] = build_discovery(site, copy)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
