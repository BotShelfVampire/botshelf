#!/usr/bin/env python3
"""Automated checks: missing JA content fields and ordinary English leakage in JA-marked bodies.

Scope: homepage category/goal/value layer, eight category hubs, recommended first-use pages,
and Robot Pilot. Technical tokens (API names, product ids, USDT, TRC20, SUBMITTED, file names,
URLs, code) are allowed in JA. Fail on ordinary English sentences inside JA-only spans.
"""
import argparse, pathlib, re, sys

TECH = re.compile(
    r"\b(Grok Bot|ChatGPT|Claude|USDT|TRC20|TRON|SUBMITTED|VERIFYING|ACTIVE|JSON|CSV|HDF5|"
    r"NVIDIA|Isaac|Lab|Teleop|SO-101|MJCF|URDF|SOFA|RDKit|n8n|Dify|Flowise|Pine|TradingView|"
    r"MT5|MQL[45]|API|SDK|HTTP|URL|HTML|CSS|JS|OTP|Yes|Copy|Description|Name|Job|Sources|"
    r"BotShelf Vampire|Gold Session Desk|Gold Morning 3|Switchboard|NY Reassess|Levels|Paths|"
    r"Position Sizer|Robot Pilot|Request Market|SELF_REPORTED|UNTESTED_RUNTIME|SIMULATION)\b"
    r"|[A-Za-z0-9_\-/]+\.(html|json|js|css|py|csv|md)"
    r"|https?://|/[a-z0-9_\-/]+/"
    r"|v?\d+\.\d+",
    re.I,
)
ORDINARY = re.compile(r"\b(the|and|with|from|your|this|that|when|where|what|which|have|has|for|are|is|not|you|can|will|into|after|before|free|paid|open|access)\b", re.I)

PAGES = [
 "index.html",
 "switchboard-cos.html", "trading-gold-morning-3.html", "trading-ny-reassess.html",
 "trading-levels-paths.html", "trading-fx-session-map.html", "trading-index-session-map.html",
 "trading-crypto-levels.html", "robot-pilot/index.html",
 "fields/index.html", "fields/healthcare/index.html", "fields/space/index.html",
 "fields/biotech/index.html", "fields/quantum/index.html",
 "library/index.html", "trading/index.html",
]

JA_SPAN = re.compile(r'<(?P<tag>\w+)(?P<attrs>[^>]*?(?:data-lang-show="ja"|data-lang="ja")[^>]*)>(?P<body>.*?)</(?P=tag)>', re.S)
# also paired: <span data-bsv-ja>...</span>

def ja_texts(html: str):
    out = []
    for m in JA_SPAN.finditer(html):
        body = re.sub(r"<[^>]+>", " ", m.group("body"))
        body = re.sub(r"\s+", " ", body).strip()
        if body: out.append(body)
    return out

def leakage(text: str):
    # strip technical tokens then look for ordinary English words leftover in a mostly-Latin run
    stripped = TECH.sub(" ", text)
    # ignore short leftovers / punctuation
    latin = re.findall(r"[A-Za-z][A-Za-z' ]{3,}", stripped)
    bad = []
    for run in latin:
        if ORDINARY.search(run) and not TECH.fullmatch(run.strip()):
            # allow single product-like CamelCase leftovers already stripped
            if len(run.split()) >= 2 or ORDINARY.search(run):
                bad.append(run.strip()[:80])
    return bad[:5]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True)
    a = ap.parse_args(); site = pathlib.Path(a.site)
    fails = []; checks = 0
    for rel in PAGES:
        p = site / rel
        if not p.exists():
            fails.append(f"missing page {rel}"); continue
        t = p.read_text()
        jas = ja_texts(t)
        checks += 1
        if rel.endswith("index.html") and "fields/" not in rel and rel != "robot-pilot/index.html":
            # homepage / hubs should have some JA
            if len(jas) < 3: fails.append(f"{rel}: too few JA spans ({len(jas)})")
        if "data-bsv-first-use" in t or rel.startswith("trading-") or rel.startswith("switchboard"):
            if not any("入れるもの" in j or "受け取るもの" in j or "動く場所" in j for j in jas):
                if "data-bsv-first-use" in t:
                    fails.append(f"{rel}: first-use JA labels missing")
        for j in jas:
            # skip pure technical / empty after strip
            leak = leakage(j)
            # allow JA that is mostly Japanese (has kana/kanji)
            if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", j):
                # still flag long ordinary English clauses
                for L in leak:
                    if len(L.split()) >= 4:
                        fails.append(f"{rel}: EN leakage in JA body: {L}")
                        break
            else:
                # JA-marked but no Japanese script — flag unless only technical
                if leak and len(j) > 24:
                    fails.append(f"{rel}: JA-marked body has no Japanese: {j[:60]}")
    # first-use pages must exist with mark
    for rel in ("switchboard-cos.html", "trading-gold-morning-3.html", "robot-pilot/index.html"):
        checks += 1
        if 'data-bsv-first-use="1"' not in (site / rel).read_text():
            fails.append(f"{rel}: first-use mark missing")
    print({"test": "ja_bodies", "checks": checks, "failures": len(fails), "fail": fails[:40]})
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
