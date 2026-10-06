#!/usr/bin/env python3
"""First-use EN/JA on free AI team pages (homepage #packs) + Robot Pilot.

Hand-crafted ITEMS override auto text. Other pack pages get a generated box from
h1 + catch EN/JA + platform (claude-/gpt-/grok). Idempotent via data-bsv-first-use="1".
"""
import argparse, pathlib, re, sys

MARK = 'data-bsv-first-use="1"'

def box(supply_en, supply_ja, receive_en, receive_ja, runs_en, runs_ja, access_en, access_ja, note_en="", note_ja=""):
    note = ""
    if note_en:
        note = (f'\n <p class="muted" data-lang-show="en"><em>Example only:</em> {note_en}</p>'
                f'\n <p class="muted" data-lang-show="ja" hidden><em>例示のみ：</em>{note_ja}</p>')
    return f'''
<section class="how-box" {MARK} aria-label="First use">
 <p class="section-label" data-lang-show="en">First use</p>
 <p class="section-label" data-lang-show="ja" hidden>初めて使うとき</p>
 <dl class="first-use-dl">
  <dt data-lang-show="en">You supply</dt><dd data-lang-show="en">{supply_en}</dd>
  <dt data-lang-show="ja" hidden>入れるもの</dt><dd data-lang-show="ja" hidden>{supply_ja}</dd>
  <dt data-lang-show="en">You receive</dt><dd data-lang-show="en">{receive_en}</dd>
  <dt data-lang-show="ja" hidden>受け取るもの</dt><dd data-lang-show="ja" hidden>{receive_ja}</dd>
  <dt data-lang-show="en">Where it runs</dt><dd data-lang-show="en">{runs_en}</dd>
  <dt data-lang-show="ja" hidden>動く場所</dt><dd data-lang-show="ja" hidden>{runs_ja}</dd>
  <dt data-lang-show="en">Access</dt><dd data-lang-show="en">{access_en}</dd>
  <dt data-lang-show="ja" hidden>アクセス</dt><dd data-lang-show="ja" hidden>{access_ja}</dd>
 </dl>{note}
</section>
'''

# Hand-crafted overrides (recommended + journey examples).
ITEMS = {
 "switchboard-cos.html": box(
  "The requests or pieces of information that are competing for attention (paste them into the chat after you set up the bot).",
  "いま注意を奪い合っている依頼や情報（ボットを用意したあとのチャットに貼る）。",
  "One short proposal of the single most useful next step. It waits for a human Yes before any send action.",
  "次の一手として最も有用な提案を一つ。人が Yes と書くまで送信しません。",
  "Your own Grok Bot (or compatible chat). You paste the team body into Description; the shop does not run it for you.",
  "ご自身の Grok Bot（または互換のチャット）。チーム本文を Description に貼ります。店側では実行しません。",
  "Free. Email register unlocks the body on this page. No key.",
  "無料。メール登録でこのページの本文が開きます。鍵は不要です。"),
 "trading-gold-morning-3.html": box(
  "Yesterday’s (or the session’s) gold high, low and close, using the input template on this page.",
  "このページの入力テンプレどおり、ゴールドの高値・安値・終値。",
  "A short morning map and exactly three scenarios. Analysis / views only — not orders, not a win-rate claim.",
  "朝の短い地図とシナリオちょうど3つ。分析・見方のみ（発注も勝率の主張もしません）。",
  "Your own Grok Bot. Paste the unlocked body into Description, then send the input template once.",
  "ご自身の Grok Bot。解除された本文を Description に貼り、入力テンプレを1回送ります。",
  "Free after email register (unlocks the body). No key. Continuity across sessions is a separate paid product (Gold Session Desk).",
  "メール登録後に無料（本文が開く）。鍵は不要。窓をまたぐ続きは別の有料商品（Gold Session Desk）。",
  "Past dogfood integers on this page (for example 4491 / 4366 / 4430) are labeled examples from a prior session — replace with live numbers.",
  "このページの過去ドッグフード整数（例: 4491 / 4366 / 4430）は以前のセッションの例示です。ライブの数字に差し替えてください。"),
 "trading-ny-reassess.html": box(
  "Your earlier gold scenario context and the updated high / low / close (or last) before New York.",
  "以前のゴールドシナリオの文脈と、NY前の新しい高値・安値・終値（または現在値）。",
  "A reassessment of whether the earlier view still holds. Analysis only.",
  "当初の見方がいまも持つかの見直し。分析のみ。",
  "Your own Grok Bot (paste Description, then chat).",
  "ご自身の Grok Bot（Description に貼ってから会話）。",
  "Free after email register. No key.",
  "メール登録後に無料。鍵は不要。"),
 "trading-levels-paths.html": box(
  "The gold price context you want leveled (session range / reference prices as the page template asks).",
  "水準化したいゴールドの価格文脈（ページのテンプレが求めるセッションレンジや参照価格）。",
  "Key prices and path scenarios above and below them. Not a single prediction.",
  "重要価格と、その上・下の値動きシナリオ。一つの予想ではありません。",
  "Your own Grok Bot.",
  "ご自身の Grok Bot。",
  "Free after email register. No key.",
  "メール登録後に無料。鍵は不要。"),
 "trading-fx-session-map.html": box(
  "FX market context for the sessions you care about (as the unlocked template asks).",
  "見たいセッション向けの FX の状況（解除後のテンプレどおり）。",
  "A map of what changed across Asia / London / New York and what matters as the next session begins. Analysis only.",
  "アジア・ロンドン・NYで何が変わったか、次の時間帯で何を見るかの整理。分析のみ。",
  "Your own Grok Bot.",
  "ご自身の Grok Bot。",
  "Free after email register. No key.",
  "メール登録後に無料。鍵は不要。"),
 "trading-index-session-map.html": box(
  "Index-market session context (as the unlocked template asks).",
  "株価指数のセッション状況（解除後のテンプレどおり）。",
  "A session map for the index: what changed and what to watch next. Analysis only.",
  "指数のセッション整理：何が変わったか、次にどこを見るか。分析のみ。",
  "Your own Grok Bot.",
  "ご自身の Grok Bot。",
  "Free after email register. No key.",
  "メール登録後に無料。鍵は不要。"),
 "trading-crypto-levels.html": box(
  "Crypto market context and the levels you want organised (as the unlocked template asks).",
  "整理したい暗号資産の状況と水準（解除後のテンプレどおり）。",
  "Key levels and possible paths if price breaks higher or lower. Analysis only.",
  "重要水準と、上抜け・下抜けした場合の道筋。分析のみ。",
  "Your own Grok Bot.",
  "ご自身の Grok Bot。",
  "Free after email register. No key.",
  "メール登録後に無料。鍵は不要。"),
 "saas-seat-waste-finder.html": box(
  "A pasted SaaS roster or invoice-style seat list (who has which seat / last activity if you have it).",
  "SaaSの名簿や請求ベースの席リスト（誰がどの席か、あれば最終利用）。",
  "A short list of seats that look unused, for a human to review. It does not cancel anything.",
  "使われていなさそうな席の短い洗い出し（人が確認する用）。解約はしません。",
  "Your own Grok Bot, Claude, or ChatGPT (paste the unlocked body into Description / instructions / Custom Instructions).",
  "ご自身の Grok Bot・Claude・ChatGPT（解除された本文を Description / 指示 / Custom Instructions に貼る）。",
  "Free after email register (unlocks the body on this page). No key. No USDT.",
  "メール登録後に無料（このページの本文が開く）。鍵不要。USDT不要。"),
 "gpt-thread-rewrite.html": box(
  "A draft social post or thread that already has the ideas but needs clearer wording.",
  "内容はあるが、文章の流れや伝わり方を整えたい書きかけのSNS投稿・スレッド。",
  "A clearer rewrite of that draft. You still review and post it yourself.",
  "読みやすく整えた書き直し。投稿するのはあなた自身です。",
  "Your own ChatGPT (preferred: Settings → Custom Instructions; Custom GPT only if your workspace allows).",
  "ご自身の ChatGPT（推奨: 設定 → カスタム指示。Custom GPT はワークスペースが許可する場合のみ）。",
  "Free after email register (unlocks the body). No key. No USDT.",
  "メール登録後に無料（本文が開く）。鍵不要。USDT不要。"),
}

RP_BOX = box(
 "One robot, one task id and one input device for a simulation session, then the counts and notes the practice-record form asks for.",
 "シミュレーション用にロボット・タスクID・入力装置を1つずつ決め、練習記録フォームが求める件数とメモ。",
 "Session-evidence and practice-record JSON you can download (self-reported). Optional private review needs a verified email; review never upgrades the record to a licence or real-hardware permission.",
 "ダウンロードできるセッション証跡と練習記録の JSON（自己申告）。任意の非公開確認にはメール確認が必要で、確認しても免許や実機操作の許可にはなりません。",
 "Your local NVIDIA Isaac Lab + Isaac Teleop simulation. BSV does not run the curriculum for you and does not redistribute NVIDIA code.",
 "ご自身の環境の NVIDIA Isaac Lab + Isaac Teleop シミュレーション。BSVはカリキュラムを代行実行せず、NVIDIAのコードも再配布しません。",
 "The Academy page is open to read. Building and keeping records in the browser needs no key; sending for BSV review needs a verified email.",
 "Academy ページの閲覧は公開。ブラウザ内の記録作成に鍵は不要。BSVへの確認依頼にはメール確認が必要です。")

CATCH_JA = re.compile(r'(<p class="catch" data-lang-show="ja"[^>]*>.*?</p>)', re.S)
CATCH_EN = re.compile(r'<p class="catch" data-lang-show="en"[^>]*>(.*?)</p>', re.S)
H1 = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)
STYLE = """
<style data-bsv-first-use-css>
.first-use-dl{display:grid;grid-template-columns:minmax(7rem,9rem) 1fr;gap:6px 14px;margin:8px 0 0}
.first-use-dl dt{margin:0;color:var(--muted,#9aa);font-weight:650;font-size:13px}
.first-use-dl dd{margin:0;font-size:14px;line-height:1.45}
@media(max-width:640px){.first-use-dl{grid-template-columns:1fr;gap:2px 0}.first-use-dl dt{margin-top:8px}}
</style>
"""
SKIP_PACK = {"paid.html", "how.html", "metals.html", "for-sellers.html", "register.html"}

def strip_html(s: str) -> str:
    s = re.sub(r'<[^>]+>', ' ', s or '')
    return re.sub(r'\s+', ' ', s).strip()

def pack_pages(site: pathlib.Path) -> list[str]:
    h = (site / "index.html").read_text()
    i = h.find('id="packs"')
    if i < 0:
        return []
    j = h.find("<section", i + 10)
    packs = h[i:j if j > 0 else i + 200000]
    out, seen = [], set()
    for href in re.findall(r'href="(/[^"#?]+\.html)"', packs):
        name = href.lstrip("/")
        if name.startswith("paid-") or name in SKIP_PACK:
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out

def platform(name: str, html: str) -> str:
    if name.startswith("claude-"):
        return "claude"
    if name.startswith("gpt-"):
        return "gpt"
    title = strip_html((re.search(r'<title>([^<]+)', html) or [None, ""])[1]).lower()
    if "claude" in title and "chatgpt" not in title:
        return "claude"
    if "chatgpt" in title or " gpt " in f" {title} ":
        return "gpt"
    return "grok"

def auto_box(name: str, html: str) -> str:
    en = strip_html((CATCH_EN.search(html) or [None, ""])[1])
    ja = strip_html((CATCH_JA.search(html) or [None, ""])[1])
    h1 = strip_html((H1.search(html) or [None, name])[1])
    if not en:
        en = f"A free AI team page: {h1}."
    if not ja:
        ja = f"無料のAIチームページ：{h1}。"
    # keep receive readable
    if len(en) > 280:
        en = en[:277] + "…"
    if len(ja) > 280:
        ja = ja[:277] + "…"
    plat = platform(name, html)
    if plat == "claude":
        supply_en = "The files, diffs, or repo context this Claude Code skill should look at (as the unlocked page describes)."
        supply_ja = "この Claude Code スキルが見るファイル・差分・リポジトリの文脈（解除後のページの説明どおり）。"
        runs_en = "Your own Claude Code session. Paste or install the unlocked skill as the page describes; BSV does not run Claude for you."
        runs_ja = "ご自身の Claude Code。解除されたスキルをページの手順どおり貼る／入れます。BSVは Claude を代行実行しません。"
    elif plat == "gpt":
        supply_en = "The draft or context the unlocked instructions ask you to paste into the chat."
        supply_ja = "解除後の指示がチャットへ貼るよう求める下書きや文脈。"
        runs_en = "Your own ChatGPT (Custom Instructions preferred; Custom GPT only if your workspace allows). BSV does not run ChatGPT for you."
        runs_ja = "ご自身の ChatGPT（推奨: カスタム指示。Custom GPT はワークスペースが許可する場合のみ）。BSVは ChatGPT を代行実行しません。"
    else:
        supply_en = "The notes, paste, or numbers the unlocked template on this page asks for."
        supply_ja = "このページの解除後テンプレが求めるメモ・貼り付け・数値。"
        runs_en = "Your own Grok Bot (or compatible chat). Paste the unlocked body into Description; the shop does not run it for you."
        runs_ja = "ご自身の Grok Bot（または互換チャット）。解除された本文を Description に貼ります。店側では実行しません。"
    access_en = "Free after email register (unlocks the body on this page). No key."
    access_ja = "メール登録後に無料（このページの本文が開く）。鍵は不要です。"
    return box(supply_en, supply_ja, en, ja, runs_en, runs_ja, access_en, access_ja)

def patch_html(path: pathlib.Path, html: str) -> bool:
    t = path.read_text()
    if MARK in t:
        return False
    m = CATCH_JA.search(t)
    if not m:
        raise SystemExit(f"add_first_use: no JA catch in {path.name}")
    t = t[: m.end()] + html + t[m.end() :]
    if "data-bsv-first-use-css" not in t:
        t = t.replace("</head>", STYLE + "</head>", 1)
    path.write_text(t)
    return True

def patch_robot_pilot(site: pathlib.Path) -> bool:
    p = site / "robot-pilot/index.html"
    t = p.read_text()
    if MARK in t:
        return False
    m = re.search(r'(<p data-lang="ja" class="lead">.*?</p>)', t, re.S)
    if not m:
        raise SystemExit("add_first_use: robot-pilot JA lead missing")
    block = RP_BOX.replace('data-lang-show="en"', 'data-lang="en"').replace('data-lang-show="ja" hidden', 'data-lang="ja"')
    t = t[: m.end()] + block + t[m.end() :]
    if "data-bsv-first-use-css" not in t:
        t = t.replace("</head>", STYLE + "</head>", 1)
    p.write_text(t)
    return True

def all_targets(site: pathlib.Path) -> dict[str, str]:
    """name -> first-use html (hand-crafted wins)."""
    targets = {}
    for name in pack_pages(site):
        path = site / name
        if not path.is_file():
            continue
        raw = path.read_text()
        if not CATCH_JA.search(raw):
            continue
        targets[name] = ITEMS.get(name) or auto_box(name, raw)
    # ensure hand-crafted always included even if not in packs scrape
    for name, html in ITEMS.items():
        if (site / name).is_file():
            targets[name] = html
    return targets

def check(site: pathlib.Path, targets: dict[str, str] | None = None):
    fails = []
    targets = targets or all_targets(site)
    for name in targets:
        p = site / name
        if not p.is_file():
            fails.append(f"{name}: missing file")
            continue
        t = p.read_text()
        if MARK not in t:
            fails.append(f"{name}: missing first-use")
            continue
        for needle in ("You supply", "You receive", "Where it runs", "Access", "入れるもの", "受け取るもの", "動く場所", "アクセス"):
            if needle not in t:
                fails.append(f"{name}: missing {needle}")
    rp = site / "robot-pilot/index.html"
    if rp.is_file() and MARK not in rp.read_text():
        fails.append("robot-pilot: missing first-use")
    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    site = pathlib.Path(a.site)
    targets = all_targets(site)
    if a.check:
        fails = check(site, targets)
        print({"test": "first_use", "pages": len(targets) + 1, "failures": len(fails), "fail": fails[:20], "fail_total": len(fails)})
        sys.exit(1 if fails else 0)
    ch = 0
    for name, html in targets.items():
        if patch_html(site / name, html):
            ch += 1
    if patch_robot_pilot(site):
        ch += 1
    fails = check(site, targets)
    print({"pass": "first_use", "changed": ch, "pages": len(targets) + 1, "failures": len(fails), "fail": fails[:20], "fail_total": len(fails)})
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
