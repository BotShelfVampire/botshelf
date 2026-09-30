from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

assert not (ROOT / "private").exists(), "private payload must not be published"
assert not list(ROOT.rglob("*.zip")), "source ZIPs must not be published"

for path in (ROOT / "public").rglob("*"):
    if path.is_file() and path.suffix in {".html", ".js", ".json", ".css"}:
        text = path.read_text(encoding="utf-8")
        for forbidden in (
            "メール登録不要",
            "元のライセンスとともに",
            "No email gate",
            "No email required",
            "window.BSV_ZIPS",
            "window.BSV_DETAILS",
        ):
            assert forbidden not in text, f"obsolete copy in {path}: {forbidden}"

print("GitHub review contract: PASS")
