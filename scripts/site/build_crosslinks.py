#!/usr/bin/env python3
"""AI toolkit <-> Library AI Team cross-links (soft "pairs with" links, not identity merges).

Edits, idempotently (marker blocks):
- /library/toolkit/<id>/        -> "Library AI Teams for this job"
- /library/toolkit/             -> "Library AI Teams" chips
- /library/teams/<team>/        -> "Agent toolkits that pair with this team"
- /library/teams/               -> "Agent toolkits by job" chips
- /library/toolkit/<runner>/     -> "Per-task Library Teams" (public page + gated full prompt) for the
                                   LangGraph / CrewAI team runners (toolkit-site-copy.json -> ai_team_runners)
- /library/<runtime>/<team>/     -> "Run this task locally" back-link to the matching runner
Mapping lives in toolkit-site-copy.json -> ai_team_links (job -> team ids).
Run after build_live_toolkit.py:  python3 scripts/site/build_crosslinks.py --site <tree>
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402

esc, T, lib_both = blt.esc, blt.T, blt.lib_both
NOTE = T("Soft links by job — a toolkit and a Team are separate items; nothing here was runtime-tested together.",
         "仕事が近いものを結んだリンクです。ツールキットとTeamは別のものとして掲載しており、組み合わせての実行検証はしていません。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--repo", default=str(blt.REPO))
    a = ap.parse_args()
    site, repo = Path(a.site), Path(a.repo)
    copy = json.loads((repo / "scripts/site/toolkit-site-copy.json").read_text())
    links = copy["ai_team_links"]
    jobs = copy["ai_jobs"]
    reg = json.loads((site / "library/registry.json").read_text())
    teams = {t["team_id"]: t for t in reg["teams"]}
    tk = json.loads((site / "library/toolkit/toolkit.v1.json").read_text())["entries"]
    for j, ids in links.items():
        missing = [i for i in ids if i not in teams]
        if j not in jobs or missing:
            raise SystemExit(f"bad ai_team_links entry {j}: {missing}")
    edits = 0
    # toolkit item pages
    for e in tk:
        p = site / f"library/toolkit/{e['id']}/index.html"
        h = p.read_text()
        lis = "".join(f'<li><a href="/library/teams/{t}/">{esc(teams[t]["title"])}</a> — <span class="muted">{esc(teams[t]["short_description"])}</span></li>' for t in links.get(e["job"], []))
        if not lis:
            continue
        blk = (f'<section class="section"><p class="section-label">Library AI Teams for this job · {esc(jobs[e["job"]]["en"])}</p>'
               f'{lib_both(T("Ready-made Library Teams that do the work this toolkit supports.", "このツールキットが支える仕事を、そのまま使えるLibraryのTeamです。"), "p")}<ul class="tk-list">{lis}</ul>{lib_both(NOTE, "p", "muted")}</section>')
        p.write_text(blt.replace_block(h, "team-links", blk, "</main>"), encoding="utf-8"); edits += 1
    # toolkit hub
    p = site / "library/toolkit/index.html"
    h = p.read_text()
    chips = "".join(f'<a class="lib-chip" href="/library/teams/{t}/">{esc(teams[t]["title"])}</a>' for t in teams)
    blk = (f'<section class="section"><p class="section-label">Library AI Teams</p>{lib_both(T("Prefer a ready-made team? These are the existing Library AI Teams; each toolkit page links the ones for its job.", "そのまま使えるTeamが良い場合は、既存のLibrary AI Teamをどうぞ。各ツールキットのページから、仕事の近いTeamに移動できます。"), "p", "muted")}'
           f'<div class="lib-chip-row"><a class="lib-chip" href="/library/teams/"><strong>All Teams ({len(teams)})</strong></a>{chips}</div></section>')
    p.write_text(blt.replace_block(h, "team-links", blk, '<section class="section how-box"><p class="section-label">How these differ'), encoding="utf-8"); edits += 1
    # team pages
    for tid, t in teams.items():
        rel = [e for e in tk if tid in links.get(e["job"], [])]
        if not rel:
            continue
        p = site / f"library/teams/{tid}/index.html"
        h = p.read_text()
        lis = "".join(f'<li><a href="{e["url"]}">{esc(e["title"])}</a> <span class="muted">({esc(e["framework"])} · {esc(jobs[e["job"]]["en"])})</span></li>' for e in rel)
        blk = (f'<section class="how-box"><p class="section-label">Agent toolkits that pair with this team</p>'
               f'{lib_both(T("Templates for the runtime around this team: memory, tool gates, local workers, orchestration. Free; source opens after free email verification.", "このTeamの周りで使うテンプレートです（記憶・ツールの安全確認・ローカル実行・オーケストレーション）。無料で、コードは無料のメール確認後に開けます。"), "p")}'
               f'<ul>{lis}</ul>{lib_both(NOTE, "p", "muted")}</section>')
        p.write_text(blt.replace_block(h, "toolkit-links", blk, "</main>"), encoding="utf-8"); edits += 1
    # per-task runners (LangGraph / CrewAI) <-> Library Team implementation pages + gated full prompts
    tk_ids = {e["id"] for e in tk}
    for rt, rn in copy.get("ai_team_runners", {}).items():
        if rn["item"] not in tk_ids:
            raise SystemExit(f"ai_team_runners item missing from toolkit: {rn['item']}")
        rows = []
        for tid, t in teams.items():
            impl = next((i for i in t["implementations"] if i.get("runtime") == rt), None)
            if not impl:
                continue
            src = f"/library/source/team-{rt}-{tid}.html"
            if not (site / src.lstrip("/")).exists():
                raise SystemExit(f"gated team source missing: {src}")
            cmd = rn["cmd"].format(task=tid)
            rows.append(f'<li><strong>{esc(t["title"])}</strong> <code>--task {esc(tid)}</code><br>'
                        f'<a href="{esc(impl["url"])}">{esc(rn["platform"])} team page</a> · <a href="{src}" data-tk-gated>Full prompt — free email verification</a> · <a href="/library/teams/{tid}/">Team overview</a></li>')
            ip = site / impl["url"].lstrip("/") / "index.html"
            ih = ip.read_text()
            iblk = (f'<section class="how-box"><p class="section-label">Run this task locally · {esc(rn["platform"])} team runner</p>'
                    f'{lib_both(T("The BSV team runner runs this task on a local model (LM Studio or Ollama), checks the required sections and saves only after your approval. Paste the team prompt from the full-text page into prompts/" + tid + ".txt.", "BSVのチームランナーで、この仕事をローカルモデル（LM StudioまたはOllama）で動かせます。必要な項目を確認し、あなたが承認したときだけ保存します。全文ページのプロンプトを prompts/" + tid + ".txt に貼り付けて使います。"), "p")}'
                    f'<p><code>{esc(cmd)}</code></p><p><a href="/library/toolkit/{rn["item"]}/"><strong>{esc(rn["platform"])} team runner →</strong></a></p>'
                    f'{lib_both(T("Not runtime tested by BSV.", "BSVでは実行検証をしていません。"), "p", "muted")}</section>')
            ip.write_text(blt.replace_block(ih, "team-runner", iblk, "</main>"), encoding="utf-8"); edits += 1
        p = site / f"library/toolkit/{rn['item']}/index.html"
        h = p.read_text()
        blk = (f'<section class="section" id="tasks"><p class="section-label">Per-task Library Teams · {len(rows)} tasks</p>'
               f'{lib_both(T("Each task id is one Library AI Team. The team page is public; the full prompt you paste into prompts/<task>.txt opens after free email verification. The runner does not include the prompts.", "タスクIDはLibrary AI Teamと1対1で対応します。Teamのページは登録なしで読めます。prompts/<task>.txt に貼り付けるプロンプト全文は、無料のメール確認後に開けます。ランナーにプロンプトは含まれていません。"), "p")}'
               f'<ul class="tk-list">{"".join(rows)}</ul>{lib_both(NOTE, "p", "muted")}</section>')
        p.write_text(blt.replace_block(h, "team-tasks", blk, "</main>"), encoding="utf-8"); edits += 1
    # teams hub
    p = site / "library/teams/index.html"
    h = p.read_text()
    chips = "".join(f'<li><a href="/library/toolkit/#job-{j}">{esc(jobs[j]["en"])}</a> <span class="muted">({sum(1 for e in tk if e["job"] == j)})</span></li>' for j in jobs if any(e["job"] == j for e in tk))
    blk = (f'<section class="how-box"><p class="section-label">Agent toolkits by job</p>{lib_both(T("Building the runtime around a team? Original BSV templates for Dots, Hugging Face, Bionic, smolagents, Letta, the OpenAI Agents SDK, and LangGraph/CrewAI runners for each team task.", "Teamの周りの実行環境を作るなら、Dots・Hugging Face・Bionic・smolagents・Letta・OpenAI Agents SDK向けのBSVオリジナルのテンプレートと、Teamの仕事ごとに動かすLangGraph・CrewAIのランナーがあります。"), "p")}'
           f'<ul>{chips}</ul><p><a href="/library/toolkit/"><strong>All AI toolkits ({len(tk)}) →</strong></a></p></section>')
    p.write_text(blt.replace_block(h, "toolkit-links", blk, "</main>"), encoding="utf-8"); edits += 1
    print(json.dumps({"pages_edited": edits, "toolkit_items": len(tk), "teams": len(teams)}))


if __name__ == "__main__":
    main()
