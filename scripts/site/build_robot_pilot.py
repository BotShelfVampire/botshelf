#!/usr/bin/env python3
"""Issue #7 tranche 1: Robot Pilot Academy landing (/robot-pilot/) on the existing Traders Library look (idempotent).

- Renders the original BSV simulation curriculum (robot-pilot/curricula/isaac-teleop-so101-sim-v1.json) and links the
  official NVIDIA docs (checked 200 on 2026-10-03; Isaac Teleop docs now live under nvidia.github.io/IsaacCapture).
- Practice record tool: builds teleop-session-evidence v0.1 + robot-pilot-profile v0.1 JSON in the browser
  (SIMULATION only, SELF_REPORTED / UNREVIEWED). Nothing is sent to BSV.
- Mission request = Request Market with area robot-pilot (/requests/?area=robot-pilot&kind=mission).
- Publishes the three schemas at their $id URLs and the curriculum JSON.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import build_live_toolkit as blt
from build_request_market import both, h8, CSS as RQ_CSS

REPO = Path(__file__).resolve().parents[2]
ORIGIN = "https://botshelfvampire.com"
SCHEMAS = {"bsv-teleop-session-evidence.schema.json": "teleop-session-evidence-v0.1.json",
           "bsv-robot-pilot-profile.schema.json": "robot-pilot-profile-v0.1.json",
           "bsv-robot-pilot-curriculum.schema.json": "robot-pilot-curriculum-v0.1.json"}
CUR = "robot-pilot/curricula/isaac-teleop-so101-sim-v1.json"
LINKS = [("Isaac Teleop documentation (NVIDIA; now published as Isaac Capture)", "https://nvidia.github.io/IsaacCapture/"),
         ("Quick start", "https://nvidia.github.io/IsaacCapture/main/getting_started/quick_start.html"),
         ("SO-101 data collection in simulation", "https://nvidia.github.io/IsaacCapture/main/getting_started/lerobot/data_collection_sim.html"),
         ("Isaac Lab installation", "https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html"),
         ("Source repository (NVIDIA/IsaacCapture, Apache-2.0)", "https://github.com/NVIDIA/IsaacCapture")]
# Task ids as listed on the official SO-101 simulation page (checked 2026-10-03).
TASK_IDS = ["IsaacContrib-Stack-Cube-SO101-IK-Abs-v0", "IsaacContrib-Stack-Cube-SO101-Joint-Teleop-v0"]
CSS = """.rp-mod{display:grid;gap:10px;padding:0;list-style:none;counter-reset:m}
.rp-mod>li{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.rp-mod h3{margin:.1rem 0 .4rem;font-size:1.05rem}
.rp-mod ul{margin:.3rem 0 .2rem 1.1rem;padding:0}
.rp-mod ul.rq-checks{list-style:none;margin-left:0}
.rp-box{border:1px solid var(--line);border-left:3px solid var(--green);border-radius:8px;padding:10px 14px;background:var(--panel)}
.rp-preview{white-space:pre;overflow:auto;max-height:420px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px;font-family:var(--mono);font-size:.8rem}
.rp-btns{display:flex;flex-wrap:wrap;gap:8px}
"""


def esc(s):
    return blt.esc(s)


def page(site, cur, css_hrefs, js_href):
    mods = []
    for m in cur["modules"]:
        crit = "".join(f'<li><label><input type="checkbox" data-rp-crit="{esc(m["id"])}:{i}"> {esc(c)}</label></li>' for i, c in enumerate(m["passCriteria"]))
        ev = "".join(f"<li>{esc(e)}</li>" for e in m["evidenceRequired"])
        mods.append(f'<li id="mod-{esc(m["id"])}"><h3>{esc(m["title"])}</h3><p>{esc(m["goal"])}</p>'
                    f'<p class="small"><strong>Evidence</strong></p><ul class="small">{ev}</ul>'
                    f'<p class="small"><strong>Pass criteria (tick what you met)</strong></p><ul class="small rq-checks">{crit}</ul></li>')
    pre = "".join(f"<li>{esc(p)}</li>" for p in cur["prerequisites"])
    links = "".join(f'<li><a href="{esc(u)}" rel="noopener" target="_blank">{esc(l)}</a></li>' for l, u in LINKS)
    opts = "".join(f'<option value="{esc(t)}"></option>' for t in TASK_IDS)
    def inp(id_, en, ja, typ="text", extra=""):
        return f'<div><label for="rp-{id_}">{both(en, ja)}</label><input type="{typ}" id="rp-{id_}" {extra}></div>'
    body = (
        '<section class="container hero bb-hero"><div><div class="eyebrow">ROBOT PILOT ACADEMY · SIMULATION FIRST</div>'
        f'<h1>{both("Practise teleoperation in simulation and keep an exact record.", "シミュレーションで遠隔操作を練習し、正確な記録を残す。")}</h1>'
        f'{both("Start in simulation, not on expensive hardware. Pick one robot, one task and one input device; practise; record each session as structured evidence; review the failures.", "高価な実機ではなく、シミュレーションから始めます。ロボット・タスク・入力装置を1つずつ決めて練習し、各セッションを構造化した記録に残し、失敗を見直します。", "p", "lead")}'
        f'{both("This curriculum is original BSV training material. It links NVIDIA's official setup and does not redistribute NVIDIA code. BSV has not run this curriculum itself yet.", "このカリキュラムはBSVオリジナルの教材です。NVIDIA公式のセットアップ手順にリンクし、NVIDIAのコードは再配布しません。BSV自身はまだこのカリキュラムを実行していません。", "p", "small")}'
        '</div><aside class="hero-stats"><div class="stat-lines">'
        f'<div>{both("Curricula", "カリキュラム")}<b>1</b></div>'
        f'<div>{both("Environment", "環境")}<b>SIM</b></div>'
        f'<div>{both("Practice records reviewed by BSV", "BSVが確認した練習記録")}<b>0</b></div>'
        '</div></aside></section>'
        '<div class="container subnav"><a class="chip" href="#boundary">' + both("What a record is not", "記録の範囲") + '</a><a class="chip" href="#curriculum">' + both("SO-101 simulation curriculum", "SO-101 シミュレーション教材") + '</a>'
        '<a class="chip" href="#record">' + both("Practice record", "練習記録") + '</a><a class="chip" href="/requests/?area=robot-pilot&amp;kind=mission">' + both("Request a mission", "ミッションをリクエスト") + '</a></div>'
        f'<section class="container bb-section" id="boundary"><h2>{both("What a BSV practice record is not", "BSVの練習記録ではないもの")}</h2><div class="rp-box"><ul>'
        f'<li>{both("Not a government licence or a manufacturer certification.", "国の免許やメーカーの認定ではありません。")}</li>'
        f'<li>{both("Not permission to operate real hardware. Real-hardware control needs the robot owner's authorisation and their local safety rules (supervisor and emergency stop where required).", "実機を操作してよいという許可ではありません。実機の操作には、ロボットの所有者の許可と、その場の安全ルール（必要に応じて監督者・非常停止）が必要です。")}</li>'
        f'<li>{both("Not proof of general ability across robots. A record covers one exact task, robot, runtime, input device and revision.", "ロボット全般の能力の証明ではありません。記録の対象は、特定のタスク・ロボット・実行環境・入力装置・リビジョンだけです。")}</li>'
        f'<li>{both("Self-reported until reviewed. BSV does not review practice records yet.", "確認されるまでは自己申告です。BSVはまだ練習記録の確認をしていません。")}</li>'
        '</ul></div></section>'
        f'<section class="container bb-section" id="curriculum"><h2>{esc(cur["title"])}</h2>'
        f'<p class="small">Runtime: {esc(cur["runtime"])} · Embodiment: {esc(cur["embodiment"])} · Input: {esc(cur["inputDevice"])} · Environment: {esc(cur["environment"])} · '
        f'<a href="/{CUR}">curriculum JSON</a> · <a href="/schemas/robot-pilot-curriculum-v0.1.json">schema</a></p>'
        f'<h3>{both("Before you start", "始める前に")}</h3><ul>{pre}</ul>'
        f'<h3>{both("Official NVIDIA references", "NVIDIA公式の資料")}</h3><ul>{links}</ul>'
        f'<ol class="rp-mod">{"".join(mods)}</ol>'
        f'<p class="small muted">{both("Completion status in this curriculum: SELF_REPORTED (minimum reviewed sessions: 0).", "このカリキュラムの修了状態: 自己申告（必要な確認済みセッション数: 0）。")}</p></section>'
        f'<section class="container bb-section" id="record"><h2>{both("Practice record (session evidence)", "練習記録（セッションの証跡）")}</h2>'
        f'<p class="small">{both("Fill this in after a simulation session. It builds two JSON files: session evidence (teleop-session-evidence v0.1, review status UNREVIEWED) and a practice record (robot-pilot-profile v0.1, SELF_REPORTED). Everything stays in this browser; nothing is sent to BSV.", "シミュレーションのセッション後に入力します。2つのJSONを作ります: セッションの証跡（teleop-session-evidence v0.1、確認状態 UNREVIEWED）と練習記録（robot-pilot-profile v0.1、SELF_REPORTED）。入力はこのブラウザーの中だけにあり、BSVには送られません。")}</p>'
        '<form class="rq-form" id="rp-form" novalidate>'
        f'<div class="rq-row">{inp("taskId", "Task id (official)", "タスクID（公式）", extra="list=\"rp-tasks\" maxlength=\"160\"")}<datalist id="rp-tasks">{opts}</datalist>'
        f'{inp("embodiment", "Embodiment", "ロボット", extra="value=\"" + esc(cur["embodiment"]) + "\" maxlength=\"160\"")}</div>'
        f'<div class="rq-row">{inp("runtime", "Runtime", "実行環境", extra="value=\"" + esc(cur["runtime"]) + "\" maxlength=\"160\"")}{inp("runtimeVersion", "Runtime version", "バージョン", extra="maxlength=\"80\"")}{inp("sourceRevision", "Source revision", "ソースのリビジョン", extra="maxlength=\"120\"")}</div>'
        f'<div class="rq-row">{inp("inputDevice", "Input device", "入力装置", extra="maxlength=\"160\" placeholder=\"XR controller / SO-101 leader\"")}{inp("pilotId", "Pilot id (pseudonymous, optional)", "パイロットID（仮名・任意）", extra="maxlength=\"80\"")}</div>'
        f'<div class="rq-row">{inp("startedAt", "Started", "開始", "datetime-local")}{inp("endedAt", "Ended", "終了", "datetime-local")}</div>'
        f'<div class="rq-row">{inp("attempted", "Episodes attempted", "試行したエピソード", "number", "min=\"0\" step=\"1\"")}{inp("successful", "Successful", "成功", "number", "min=\"0\" step=\"1\"")}{inp("failed", "Failed", "失敗", "number", "min=\"0\" step=\"1\"")}{inp("recovery", "Recovery episodes", "リカバリー", "number", "min=\"0\" step=\"1\"")}</div>'
        f'<div class="rq-row">{inp("artifactType", "Dataset type", "データの種類", extra="value=\"HDF5\" maxlength=\"40\"")}{inp("artifactRef", "Dataset reference (path or id)", "データの場所・ID", extra="maxlength=\"500\"")}{inp("artifactSha", "Dataset sha256 (optional)", "sha256（任意）", extra="maxlength=\"64\"")}</div>'
        f'<div><label for="rp-safetyEvents">{both("Safety / reset events (one per line)", "安全・リセットの出来事（1行に1件）")}</label><textarea id="rp-safetyEvents" maxlength="4000"></textarea></div>'
        f'<div><label for="rp-note">{both("Notes: failures, limitations, what to improve", "メモ: 失敗・制約・次に直すこと")}</label><textarea id="rp-note" maxlength="2000"></textarea></div>'
        f'<p class="small muted">{both("Environment is fixed to SIMULATION. Pass criteria ticked in the curriculum above are stored in metrics.", "環境はSIMULATIONに固定です。上のカリキュラムで付けたチェックは metrics に入ります。")}</p>'
        f'<div class="rp-btns"><button type="submit" class="btn primary">{both("Check record", "記録を確認")}</button>'
        f'<button type="button" class="btn" id="rp-dl-ev">{both("Download session evidence", "証跡をダウンロード")}</button>'
        f'<button type="button" class="btn" id="rp-dl-rec">{both("Download practice record", "練習記録をダウンロード")}</button>'
        f'<button type="button" class="btn" id="rp-save">{both("Save in this browser", "このブラウザーに保存")}</button></div>'
        '<p class="rq-msg" id="rp-msg" role="status"></p><p class="small muted" id="rp-saved"></p>'
        '<pre class="rp-preview" id="rp-preview" aria-label="JSON preview"></pre></form>'
        f'<p class="small"><a href="/schemas/teleop-session-evidence-v0.1.json">teleop-session-evidence v0.1</a> · <a href="/schemas/robot-pilot-profile-v0.1.json">robot-pilot-profile v0.1</a></p></section>'
        f'<section class="container bb-section" id="mission"><h2>{both("Need a pilot or a dataset? Request a mission", "パイロットやデータが必要なら: ミッションをリクエスト")}</h2>'
        f'<p>{both("Missions go through the Request Market (request only, no escrow). Describe the task, robot, teleop interface, environment, data and episode target. Real-hardware missions stay under the robot owner's authorisation and safety rules.", "ミッションはRequest Market（リクエストのみ・エスクローなし）から送ります。タスク・ロボット・遠隔操作の方法・環境・必要なデータ・エピソード数を書いてください。実機のミッションは、ロボットの所有者の許可と安全ルールのもとで行います。")}</p>'
        f'<p><a class="btn primary" href="/requests/?area=robot-pilot&amp;kind=mission">{both("Request a mission", "ミッションをリクエスト")}</a></p></section>'
        f'<script type="application/json" id="rp-curriculum-data">{json.dumps({"curriculumId": cur["curriculumId"], "modules": [{"id": m["id"], "passCriteria": m["passCriteria"]} for m in cur["modules"]]}, ensure_ascii=False).replace("</", "<\\/")}</script>'
    )
    extra = "".join(f'<link rel="stylesheet" href="{h}">' for h in css_hrefs) + f'<script src="{js_href}" defer></script>'
    html_ = blt.trader_shell(site, "Robot Pilot Academy — simulation-first teleoperation practice · BotShelf Vampire",
                             "Simulation-first teleoperation practice: an original SO-101 Isaac Teleop simulation curriculum, a schema-backed practice record built in your browser, and mission requests.",
                             "/robot-pilot/", body, extra_head=extra)
    foot = ('<footer class="site-footer"><div class="container"><p data-lang="en">Original BSV training material. NVIDIA, Isaac, Isaac Lab and Isaac Teleop belong to NVIDIA; BSV is not affiliated with or endorsed by NVIDIA. A BSV practice record is not a licence, a certification or permission to operate real hardware.</p>'
            '<p data-lang="ja">BSVオリジナルの教材です。NVIDIA・Isaac・Isaac Lab・Isaac Teleop はNVIDIAのものであり、BSVはNVIDIAと提携・推奨の関係にありません。BSVの練習記録は、免許・認定・実機操作の許可ではありません。</p></div></footer>')
    html_ = re.sub(r'<footer class="site-footer">.*?</footer>', foot, html_, count=1, flags=re.S)
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "BotShelf Vampire", "item": ORIGIN + "/"},
        {"@type": "ListItem", "position": 2, "name": "Robot Pilot Academy", "item": ORIGIN + "/robot-pilot/"}]}
    return html_.replace("</head>", f'<script type="application/ld+json">{json.dumps(crumbs, separators=(",", ":"))}</script></head>', 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); a = ap.parse_args()
    site = Path(a.site)
    blt.assets(site)
    cur = json.loads((REPO / CUR).read_text())
    d = site / "robot-pilot"; d.mkdir(exist_ok=True)
    for old in d.glob("robot-pilot.*"):
        old.unlink()
    js = (REPO / "scripts/site/robot_pilot_record.js").read_text()
    css_n, js_n = f"robot-pilot.{h8(CSS)}.css", f"robot-pilot.{h8(js)}.js"
    (d / css_n).write_text(CSS); (d / js_n).write_text(js)
    rq_css = [p.name for p in (site / "requests").glob("request-market.*.css")]
    if len(rq_css) != 1:
        sys.exit("run build_request_market.py first (needs the shared form CSS)")
    (d / "index.html").write_text(page(site, cur, [f"/requests/{rq_css[0]}", f"/robot-pilot/{css_n}"], f"/robot-pilot/{js_n}"))
    (d / "curricula").mkdir(exist_ok=True)
    (site / CUR).write_text((REPO / CUR).read_text())
    sd = site / "schemas"; sd.mkdir(exist_ok=True)
    for src, dst in SCHEMAS.items():
        t = (REPO / "schemas" / src).read_text()
        if json.loads(t)["$id"] != f"{ORIGIN}/schemas/{dst}":
            sys.exit(f"schema $id mismatch for {src}")
        (sd / dst).write_text(t)
    smp = site / "sitemap.xml"; s = smp.read_text(); u = ORIGIN + "/robot-pilot/"
    if f"<loc>{u}</loc>" not in s:
        smp.write_text(s.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>2026-10-04</lastmod></url>\n</urlset>"))
    print(json.dumps({"robot_pilot_page": "/robot-pilot/", "modules": len(cur["modules"]), "js": js_n, "css": css_n, "schemas": len(SCHEMAS)}))


if __name__ == "__main__":
    main()
