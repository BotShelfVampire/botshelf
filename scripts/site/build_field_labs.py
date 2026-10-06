#!/usr/bin/env python3
"""Add BSV's original static Field Labs to an existing full site tree.

This is an additive generator, never a standalone production deploy tree.
Usage: python3 scripts/site/build_field_labs.py --site FULL_STAGING_TREE
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

FIELDS = [
    ("healthcare", "Medical robotics pilot planner", "医療ロボティクスの検証計画", "Turn a use case into a research or simulation validation plan.", "用途と成功条件から、研究・シミュレーションの検証計画を作成。"),
    ("robotics", "Planar 2R IK playground", "平面2R IKプレイグラウンド", "Solve elbow-down IK, inspect manipulability, export a CSV.", "肘下がりIKを解き、可操作性を見てCSVに書き出す。"),
    ("data", "CSV profile playground", "CSVプロフィール・プレイグラウンド", "Paste a CSV and profile nulls, distinct counts and type guesses.", "CSVを貼り、欠損・ユニーク数・型推定をプロフィールする。"),
    ("space", "Satellite observation designer", "衛星データの観測プラン", "Compare public satellite data against your observation constraints.", "観測したい現象と条件から公開衛星データを比較。"),
    ("biotech", "Research reproducibility worksheet", "研究データの再現性チェック", "Identify missing evidence and export an analysis record.", "不足している記録を見つけ、再現のための解析記録を出力。"),
    ("ai", "Context budget playground", "コンテキスト予算プレイグラウンド", "Estimate rough tokens for a prompt or context pack against common windows.", "プロンプトやコンテキストパックの概算トークンを、よくある枠と照らす。"),
    ("trading", "Risk & R-multiple playground", "リスクとR倍数プレイグラウンド", "Size a trade from equity, risk %, entry and stop; export a plan CSV.", "資金・リスク％・エントリー・損切りから数量を出し、計画CSVを書き出す。"),
    ("quantum", "Quantum state explorer", "量子状態を動かす実験室", "Explore how phase changes ideal X and Z measurement probabilities.", "位相によるX・Z測定の確率の違いを、その場で操作。"),
]

def build(site: Path, source: Path) -> dict:
    available = [(key, en, ja, desc_en, desc_ja) for key, en, ja, desc_en, desc_ja in FIELDS
                 if (source / key / "index.html").is_file() and (source / key / "app.js").is_file()]
    if not available:
        raise ValueError("No complete field tools found")
    files = [p for p in source.rglob("*") if p.is_file() and p.suffix in {".html", ".css", ".js"}]
    assets = {p: p.with_name(p.stem + "." + hashlib.sha256(p.read_bytes()).hexdigest()[:12] + p.suffix)
              for p in files if p.suffix in {".css", ".js"}}
    output = site / "labs"
    for src in files:
        dst = output / assets.get(src, src).relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix != ".html":
            dst.write_bytes(src.read_bytes())
            continue
        markup = src.read_text(encoding="utf-8")
        def rewrite(match):
            raw = match.group(2)
            if raw.startswith(("/", "#", "https:", "http:", "mailto:")):
                return match.group(0)
            target = (src.parent / raw.split("?")[0]).resolve()
            if target in assets:
                return match.group(1) + raw.replace(target.name, assets[target].name) + match.group(3)
            return match.group(0)
        markup = re.sub(r'((?:src|href)=")([^"<>]+)(")', rewrite, markup)
        if len(available) != len(FIELDS) and src == source / "index.html":
            for key, *_ in FIELDS:
                if key not in {row[0] for row in available}:
                    markup = re.sub(r'<article class="card">(?:(?!<article).)*?href="' + key + r'/".*?</article>', '', markup, flags=re.S)
        dst.write_text(markup, encoding="utf-8")
    entries = [{"id": "bsv-field-lab-" + key, "field": key, "url": "/labs/" + key + "/",
                "title": {"en": en, "ja": ja}, "summary": {"en": desc_en, "ja": desc_ja},
                "type": "Interactive tool", "status": "browser tool", "requires_account": False}
               for key, en, ja, desc_en, desc_ja in available]
    manifest = {"schema_version": 1, "hub": "/labs/", "entries": entries}
    (output / "catalog.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tools = site / "trading/tools/index.html"
    if tools.is_file():
        html = tools.read_text(encoding="utf-8")
        if 'data-bsv-lab="trading-risk"' not in html and 'class="container subnav"' in html:
            chip = (
                '<a class="chip" data-bsv-lab="trading-risk" href="/labs/trading/">'
                '<span data-lang="en">Risk &amp; R lab</span>'
                '<span data-lang="ja">リスクとRのラボ</span></a>'
            )
            html = html.replace('<div class="container subnav">', '<div class="container subnav">' + chip, 1)
            tools.write_text(html, encoding="utf-8")

    toolkit = site / "library/toolkit/index.html"
    if toolkit.is_file():
        html = toolkit.read_text(encoding="utf-8")
        if 'data-bsv-lab="ai-context"' not in html:
            chip = (
                '<a class="chip" data-bsv-lab="ai-context" href="/labs/ai/">'
                '<span data-lang="en">Context budget lab</span>'
                '<span data-lang="ja">コンテキスト予算ラボ</span></a>'
            )
            if 'class="container subnav"' in html:
                html = html.replace('<div class="container subnav">', '<div class="container subnav">' + chip, 1)
            elif '<main' in html:
                html = html.replace('<main', chip + '<main', 1)
            else:
                html = chip + html
            toolkit.write_text(html, encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2] / "field-labs")
    args = parser.parse_args()
    print(json.dumps(build(args.site.resolve(), args.source.resolve()), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
