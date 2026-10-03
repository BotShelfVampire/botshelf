#!/usr/bin/env python3
"""Issue #8 tranche 1: discovery and trust infrastructure (idempotent).

- robots.txt: OAI-SearchBot (search) allowed with the same Disallow list as `*`;
  GPTBot (training crawl) disallowed. robots.txt is not access control; gated
  pages stay gated at the app/auth layer.
- sitemap.xml: drop entries that are noindex or whose canonical names another URL.
- canonical: add a self-canonical to sitemap pages that have none.
- llms.txt: append one marked block of public, stable URLs (each checked: file
  exists, indexable, in sitemap or a public machine-readable file).
- /.well-known/bsv-trust.json: every fact carries the production page it was
  read from and the exact sentence; the build fails if a sentence is missing.
  Figures are counted from /trading/catalog.json and cross-checked with the page.

No wallet, price, split, payout, auth or entitlement logic is touched.
"""
import argparse, html, json, re, sys, datetime
from pathlib import Path

ORIGIN = "https://botshelfvampire.com"
AI_BEGIN = "# BSV-AI-CRAWLERS:BEGIN"
AI_END = "# BSV-AI-CRAWLERS:END"
LL_BEGIN = "<!-- BSV-DISCOVERY:BEGIN -->"
LL_END = "<!-- BSV-DISCOVERY:END -->"

# (key, page, exact English sentence that must appear in the page's visible text)
FACTS = [
    ("payments", "for-buyers.html", "Pay with USDT TRC20. Card is not available."),
    ("seller_split_payout", "for-sellers.html", "Paid listings: 80% you / 20% shop of a confirmed eligible sale; payout within 7 business days (Monday–Friday UTC, excluding configured holidays)."),
    ("payout_holds", "for-sellers.html", "Why can a payout be held? Payment still under review; dispute/refund pending; fraud concern; invalid payout wallet; product unavailable/broken; seller review required."),
    ("payout_hold_reason", "for-sellers.html", "A hold must have a recorded reason."),
    ("price_floor", "for-sellers.html", "Paid price floor: From $15/mo (15 USDT). Not a fixed fee — sellers choose any monthly amount at or above 15."),
    ("payout_network", "for-sellers.html", "Network is locked to TRC20 USDT payouts."),
    ("no_private_key", "for-sellers.html", "BSV never asks for a private key or seed phrase."),
    ("ib_link_fee", "for-sellers.html", "Important: publishing with an IB link costs 250 USDT per month (every 30 days, paid to BSV). Without an IB link, publishing is free."),
    ("free_access", "for-buyers.html", "Free content: verify your email with the 6-digit code, then access it. No USDT payment is required."),
    ("paid_access_start", "for-buyers.html", "Access starts after confirmation — not when you click send."),
    ("paid_access_expiry", "for-buyers.html", "Expiry: 30 days after confirmation. Renew early: leftover days are kept."),
    ("refunds", "for-buyers.html", "No refunds."),
    ("public_contact", "for-sellers.html", "Optional public X / public contact email are off by default and never equal your login email unless you opt in separately."),
    ("support_email", "for-buyers.html", "support@botshelfvampire.com"),
]


def visible_text(p: Path) -> str:
    t = p.read_text(errors="ignore")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def page_url(rel: str) -> str:
    return ORIGIN + "/" + rel


def head_meta(t: str):
    rb = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)', t, re.I)
    cn = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', t, re.I)
    return (rb.group(1).lower() if rb else ""), (cn.group(1) if cn else None)


def url_to_file(site: Path, u: str) -> Path:
    p = u[len(ORIGIN):]
    if p.endswith("/"):
        p += "index.html"
    return site / p.lstrip("/")


def robots(site: Path) -> dict:
    rb = site / "robots.txt"
    t = rb.read_text()
    t = re.sub(re.escape(AI_BEGIN) + r".*?" + re.escape(AI_END) + r"\n*", "", t, flags=re.S)
    dis = [l.strip() for l in t.splitlines() if l.strip().lower().startswith("disallow:")]
    block = [AI_BEGIN,
             "# Search discovery (OAI-SearchBot) may crawl public pages; it gets the same Disallow list as *.",
             "# Model-training crawl (GPTBot) is disallowed by default (owner may change this).",
             "# robots.txt is not access control: gated source stays gated at the app/auth layer.",
             "User-agent: OAI-SearchBot", "Allow: /", *dis, "",
             "User-agent: GPTBot", "Disallow: /", AI_END, ""]
    i = t.find("User-agent: *")
    t = (t[:i] + "\n".join(block) + "\n" + t[i:]) if i >= 0 else (t.rstrip() + "\n\n" + "\n".join(block))
    rb.write_text(t)
    return {"robots_disallow_copied": len(dis)}


def sitemap_and_canonical(site: Path) -> dict:
    smp = site / "sitemap.xml"
    s = smp.read_text()
    removed, canon_added = [], []
    def keep(m):
        u = m.group(1)
        f = url_to_file(site, u)
        if f.suffix == ".html" and f.exists():
            rb, cn = head_meta(f.read_text(errors="ignore"))
            if "noindex" in rb or (cn and cn != u):
                removed.append(u)
                return ""
        return m.group(0)
    s = re.sub(r"[ \t]*<url><loc>([^<]+)</loc>.*?</url>\n?", keep, s, flags=re.S)
    smp.write_text(s)
    for u in re.findall(r"<loc>([^<]+)</loc>", s):
        f = url_to_file(site, u)
        if f.suffix != ".html" or not f.exists():
            continue
        t = f.read_text(errors="ignore")
        if head_meta(t)[1] is None and "</title>" in t:
            t = t.replace("</title>", f'</title><link rel="canonical" href="{u}">', 1)
            f.write_text(t)
            canon_added.append(u)
    return {"sitemap_removed": removed, "canonical_added": canon_added}


def trust(site: Path, today: str) -> dict:
    facts, missing = {}, []
    for key, page, sent in FACTS:
        if sent not in visible_text(site / page):
            missing.append((key, page))
        facts[key] = {"text": sent, "source": page_url(page)}
    cat = json.loads((site / "trading/catalog.json").read_text())
    n = len(cat)
    bundled = sum(1 for i in cat if i.get("distribution") == "bundled")
    hosted = sum(1 for i in cat if i.get("distribution") == "author-hosted")
    rt = sum(1 for i in cat if i.get("runtime_tested") is True)
    comp = sum(1 for i in cat if i.get("compiled") is True)
    tt = visible_text(site / "trading/index.html")
    for label, v in [("free resources", n), ("Source bundles", bundled), ("Author-hosted sources", hosted)]:
        if not re.search(rf"{v} {re.escape(label)}|{re.escape(label)} [^0-9]*{v}\b", tt):
            missing.append(("catalog:" + label, "trading/index.html"))
    if not re.search(rf"Runtime-tested by BSV [^0-9]*{rt}\b", tt):
        missing.append(("catalog:runtime_tested", "trading/index.html"))
    if missing:
        raise SystemExit(f"trust manifest: production sentence/figure not found: {missing}")
    m = {
        "schemaVersion": "0.1",
        "brand": "BotShelf Vampire",
        "canonicalUrl": ORIGIN + "/",
        "supportEmail": "support@botshelfvampire.com",
        "generatedAt": today,
        "method": "Each fact below is the exact sentence on the linked production page at build time; the build fails if a sentence is no longer there. If a page and this file disagree, the page and the current checkout win.",
        "payments": {"currentRail": "USDT", "network": "TRC20", "card": False, "fact": facts["payments"]},
        "sellerEconomics": {"sellerSharePercent": 80, "bsvSharePercent": 20, "payoutWithinBusinessDays": 7,
                            "fact": facts["seller_split_payout"], "holds": facts["payout_holds"],
                            "holdReason": facts["payout_hold_reason"], "payoutNetwork": facts["payout_network"]},
        "listingRules": {"paidMonthlyMinimumUSDT": 15, "priceFloor": facts["price_floor"],
                         "ibLinkMonthlyFeeUSDT": 250, "ibLink": facts["ib_link_fee"]},
        "buyerAccess": {"free": facts["free_access"], "paidStart": facts["paid_access_start"],
                        "paidExpiry": facts["paid_access_expiry"], "refunds": facts["refunds"]},
        "security": {"privateKeys": facts["no_private_key"]},
        "publicContactPolicy": facts["public_contact"],
        "tradersLibrary": {"source": ORIGIN + "/trading/catalog.json", "entries": n, "bundled": bundled,
                           "authorHosted": hosted, "compiledByBSV": comp, "runtimeTestedByBSV": rt,
                           "note": "Counted from the public catalogue at build time; matches the figures on " + ORIGIN + "/trading/"},
        "policies": {"buyers": page_url("for-buyers.html"), "sellers": page_url("for-sellers.html"),
                     "privacy": page_url("privacy.html")},
    }
    d = site / ".well-known"
    d.mkdir(exist_ok=True)
    (d / "bsv-trust.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n")
    return {"trust_facts": len(FACTS), "catalog": [n, bundled, hosted, comp, rt]}


LLMS_LINKS = [
    ("Recipe builder (edit recipe blocks, generate chart-tool starters in the browser)", "trading/build/"),
    ("Traders Library", "trading/"),
    ("Request Market (real, reviewed requests only; JSON at /.netlify/functions/demand-request?op=public)", "requests/"),
    ("Buyer guide", "for-buyers.html"),
    ("Seller guide", "for-sellers.html"),
    ("Privacy", "privacy.html"),
    ("About", "about.html"),
]


def llms(site: Path, today: str) -> dict:
    p = site / "llms.txt"
    t = p.read_text()
    t = re.sub(r"\n*" + re.escape(LL_BEGIN) + r".*?" + re.escape(LL_END) + r"\n*", "\n", t, flags=re.S).rstrip() + "\n"
    locs = set(re.findall(r"<loc>([^<]+)</loc>", (site / "sitemap.xml").read_text()))
    lines = []
    for label, rel in LLMS_LINKS:
        u = ORIGIN + "/" + rel
        f = url_to_file(site, u)
        if not f.exists():
            raise SystemExit(f"llms: missing {rel}")
        rb, _ = head_meta(f.read_text(errors="ignore"))
        if "noindex" in rb or u not in locs:
            raise SystemExit(f"llms: {rel} is not an indexable sitemap URL")
        lines.append(f"- {label}: {u}")
    block = [LL_BEGIN, "", f"## Start here, rules and trust facts ({today})", *lines,
             f"- Trust facts (machine-readable; each fact quotes its production page): {ORIGIN}/.well-known/bsv-trust.json",
             f"- Sitemap: {ORIGIN}/sitemap.xml",
             "- Gated source is not listed here and needs a verified email session; this file does not replace robots.txt, sitemap.xml or canonical URLs.",
             "", LL_END]
    p.write_text(t + "\n" + "\n".join(block) + "\n")
    return {"llms_links": len(lines)}


def org_email(site: Path) -> dict:
    """Homepage Organization JSON-LD: add the support email (already public on every policy page)."""
    p = site / "index.html"
    t = p.read_text()
    changed = 0
    def fix(m):
        nonlocal changed
        try:
            d = json.loads(m.group(2))
        except Exception:
            return m.group(0)
        for node in d.get("@graph", []) if isinstance(d, dict) else []:
            if node.get("@type") == "Organization" and node.get("@id") == ORIGIN + "/#org" and "email" not in node:
                node["email"] = "support@botshelfvampire.com"
                changed += 1
        return m.group(1) + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + m.group(3) if changed else m.group(0)
    t2 = re.sub(r'(<script[^>]+application/ld\+json[^>]*>)(.*?)(</script>)', fix, t, flags=re.S)
    if t2 != t:
        p.write_text(t2)
    return {"org_email_added": changed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    a = ap.parse_args()
    site = Path(a.site)
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    out = {}
    out.update(robots(site))
    out.update(sitemap_and_canonical(site))
    out.update(trust(site, today))
    out.update(llms(site, today))
    out.update(org_email(site))
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
