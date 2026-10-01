from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

assert not (ROOT / "private").exists(), "private payload must not be published"
assert not list(ROOT.rglob("*.zip")), "source archives must not be in the review tree"
assert not list(ROOT.rglob("*.mq4")), "MT4 source must not be in the review tree"
assert not list(ROOT.rglob("*.mq5")), "MT5 source must not be in the review tree"

public = ROOT / "public"
assert public.exists(), "public review UI is missing"
assert not (public / "trading" / "sources").exists()
assert not (public / "trading" / "downloads").exists()

for path in public.rglob("*"):
    if path.is_file() and path.suffix.lower() in {".html", ".js", ".json", ".css"}:
        text = path.read_text(encoding="utf-8")
        for forbidden in (
            "window.BSV_ZIPS",
            "window.BSV_DETAILS",
            "メール登録不要",
            "No email required",
            "No email gate",
        ):
            assert forbidden not in text, f"obsolete/source-bearing marker in {path}: {forbidden}"

rules = (ROOT / "docs" / "OWNER-RULES-V3.md").read_text(encoding="utf-8")
for required in ("Monthly subscription only", "USDT only", "TRC20 only", "Seller share", "BSV fee"):
    assert required in rules, f"missing v3 rule: {required}"

print("Review branch contract: PASS")
