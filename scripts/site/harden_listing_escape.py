#!/usr/bin/env python3
"""Harden user-supplied listing fields on every render surface (idempotent; run on a stage root).

Server (netlify/functions/_lib):
  - products.safePublicXUrl(): public_x_url must be https://(x|twitter).com/<handle>[/...] or it is dropped,
    both when a listing is saved (engine.handleListingCreate) and when it is shown (products.publicListingView,
    which also covers records saved before this fix).
  - engine.handleListingCreate: product_type coerced to a short [A-Za-z0-9_ -] token; prerequisites to <=12 strings.
Client:
  - site/js/commerce-client.v20261007.js (new immutable name): esc() also escapes ', safeUrl() allows only
    https:// or same-site relative hrefs (no javascript:/data:), public email must look like an email;
    BSVCommerce._render exposes esc/safeUrl/cardHtml/sellerBits for the regression test.
  - operator: listing ids shown in the seller registry; "Listing review" box rejects a listing through the
    existing admin endpoint POST /operator/listing (x-admin-secret). Auth is unchanged.
  - the 9 pages that load commerce-client are repointed to the new file.
Emails are text/plain with CR/LF stripped from the subject, so no change there.
"""
import argparse, pathlib, re, sys

OLD_JS = "commerce-client.v20260912c.js"
NEW_JS = "commerce-client.v20261007.js"

SAFE_X_FN = '''
// Seller-supplied public X link: only https://(x|twitter).com/<handle>[/path]; anything else is dropped.
function safePublicXUrl(u) {
  u = String(u == null ? "" : u).trim().slice(0, 200);
  return /^https:\\/\\/(?:www\\.|mobile\\.)?(?:x|twitter)\\.com\\/[A-Za-z0-9_]{1,30}(?:[\\/?#][^\\s<>"'`\\\\]*)?$/.test(u) ? u : "";
}
'''

def sub_once(text, old, new, label):
    if new in text:
        return text
    n = text.count(old)
    if n != 1:
        sys.exit(f"harden_listing_escape: {label}: expected 1 match, got {n}")
    return text.replace(old, new)

def patch_products(p):
    t = p.read_text()
    if "function safePublicXUrl" not in t:
        t = sub_once(t, "function publicListingView(listing) {", SAFE_X_FN.lstrip("\n") + "\nfunction publicListingView(listing) {", "products.fn")
    t = sub_once(t,
        "  if (listing.show_x_publicly && listing.public_x_url) {\n    item.public_x_url = String(listing.public_x_url).slice(0, 200);\n  }",
        "  if (listing.show_x_publicly && safePublicXUrl(listing.public_x_url)) {\n    item.public_x_url = safePublicXUrl(listing.public_x_url);\n  }",
        "products.view")
    t = sub_once(t, "  plainText: plainText\n};", "  plainText: plainText,\n  safePublicXUrl: safePublicXUrl\n};", "products.exports")
    p.write_text(t)

def patch_engine(p):
    t = p.read_text()
    t = sub_once(t,
        '    product_type: listingType === "PAID" ? (body.product_type || "") : "DOWNLOADABLE_SOURCE",\n    price_micro: listingType === "FREE" ? 0 : priceMicro,\n    status: statusWanted',
        '    product_type: listingType === "PAID" ? String(body.product_type || "").replace(/[^A-Za-z0-9_ -]/g, "").slice(0, 60) : "DOWNLOADABLE_SOURCE",\n    price_micro: listingType === "FREE" ? 0 : priceMicro,\n    status: statusWanted',
        "engine.product_type")
    t = sub_once(t,
        "    prerequisites: body.prerequisites || [],\n    limitations: String(body.limitations",
        "    prerequisites: Array.isArray(body.prerequisites) ? body.prerequisites.slice(0, 12).map(function (x) { return String(x == null ? \"\" : x).slice(0, 200); }) : [],\n    limitations: String(body.limitations",
        "engine.prereq")
    t = sub_once(t,
        '    public_x_url: body.show_x_publicly ? String(body.public_x_url || "").slice(0, 200) : "",',
        '    public_x_url: body.show_x_publicly ? products.safePublicXUrl(body.public_x_url) : "",',
        "engine.public_x_url")
    p.write_text(t)

CLIENT_REPL = [
    ("esc", '''  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }''', '''  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }
  // href guard: https:// or a same-site relative path only (no javascript:, data:, //host).
  function safeUrl(u, fallback) {
    var s = String(u == null ? "" : u).trim();
    if (/^https:\\/\\/[^\\s<>"'`]+$/i.test(s)) return s;
    if (s && !/^[a-z][a-z0-9+.\\-]*:/i.test(s) && !/^\\/\\//.test(s) && !/[\\s<>"'`\\\\]/.test(s)) return s;
    return fallback == null ? "" : fallback;
  }
  function safeEmail(e) {
    var s = String(e == null ? "" : e).trim();
    return /^[^\\s@<>"'`]+@[^\\s@<>"'`]+\\.[^\\s@<>"'`]+$/.test(s) ? s : "";
  }'''),
    ("access", '''"<a class=\\"btn-fat btn-solid\\" href=\\"" + esc(p.access_url || p.page || "key.html") + "\\">Access now</a>"''',
               '''"<a class=\\"btn-fat btn-solid\\" href=\\"" + esc(safeUrl(p.access_url || p.page || "key.html", "key.html")) + "\\">Access now</a>"'''),
    ("x", '''    if (item.public_x_url) {
      bits.push("<a href=\\"" + esc(item.public_x_url) + "\\" rel=\\"noopener noreferrer\\" target=\\"_blank\\">X</a>");
    }
    if (item.public_email) {
      bits.push("<a href=\\"mailto:" + esc(item.public_email) + "\\">" + esc(item.public_email) + "</a>");
    }''', '''    var xUrl = /^https:\\/\\//i.test(String(item.public_x_url || "")) ? safeUrl(item.public_x_url) : "";
    if (xUrl) {
      bits.push("<a href=\\"" + esc(xUrl) + "\\" rel=\\"noopener noreferrer nofollow\\" target=\\"_blank\\">X</a>");
    }
    var pubEmail = safeEmail(item.public_email);
    if (pubEmail) {
      bits.push("<a href=\\"mailto:" + esc(pubEmail) + "\\">" + esc(pubEmail) + "</a>");
    }'''),
    ("cardhref", '''"\\" href=\\"" + esc(href) + "\\">" + cta + "</a>" +''',
                 '''"\\" href=\\"" + esc(safeUrl(href, "#")) + "\\">" + cta + "</a>" +'''),
    ("opsellers", '''var names = (s.listings || []).map(function (l) { return esc(l.name) + " [" + esc(l.status) + "]"; }).join("<br>");''',
                  '''var names = (s.listings || []).map(function (l) { return esc(l.name) + " [" + esc(l.status) + "] <code class=\\"mono\\">" + esc(l.id) + "</code>"; }).join("<br>");'''),
    ("opreject", '''    document.querySelectorAll("[data-op-filter]").forEach(function (btn) {''',
                 '''    var lrej = el("op-lst-reject");
    if (lrej) lrej.addEventListener("click", function () {
      var id = val("op-lst-id");
      if (!/^lst_[a-z0-9]{6,64}$/i.test(id)) { text("op-lst-status", "Enter a listing id (lst_...)."); return; }
      call("POST", "/operator/listing", { listing_id: id, action: "reject", reason: val("op-lst-reason") }, adminHeaders()).then(function (r) {
        text("op-lst-status", r.body && r.body.ok ? (id + " → " + r.body.status) : ("Reject failed: " + ((r.body && (r.body.reason || r.body.error)) || r.status)));
        loadRegs();
      });
    });
    document.querySelectorAll("[data-op-filter]").forEach(function (btn) {'''),
    ("expose", '''    mountPublicCatalog: mountPublicCatalog
  };''', '''    mountPublicCatalog: mountPublicCatalog,
    _render: { esc: esc, safeUrl: safeUrl, safeEmail: safeEmail, cardHtml: cardHtml, sellerBits: sellerBits, table: table }
  };'''),
]

OP_HTML_OLD = '<h2>Seller registry</h2>\n<div id="op-sellers"></div>\n'
OP_HTML_NEW = OP_HTML_OLD + '''<section class="strip" id="op-listing-review">
 <h2>Listing review</h2>
 <p class="muted">Reject a submitted listing (spam, probe or rule breach). Uses the admin key above; the seller gets the standard text-only notice.</p>
 <label for="op-lst-id">Listing id (from the seller registry)</label>
 <input id="op-lst-id" class="mono" maxlength="70" autocomplete="off">
 <label for="op-lst-reason">Reason sent to the seller</label>
 <input id="op-lst-reason" maxlength="500" value="Rejected: the listing has no product content (test/probe submission).">
 <p class="btn-row"><button type="button" class="btn" id="op-lst-reject">Reject listing</button></p>
 <p id="op-lst-status" class="muted" aria-live="polite"></p>
</section>
'''

def patch_client(site):
    js = site / "js"
    new = js / NEW_JS
    if not new.exists():
        t = (js / OLD_JS).read_text()
        for label, old, rep in CLIENT_REPL:
            t = sub_once(t, old, rep, "client." + label)
        new.write_text(t)
    t = new.read_text()
    for label, old, rep in CLIENT_REPL:
        if rep not in t:
            sys.exit(f"harden_listing_escape: {NEW_JS} missing {label}")
    pages = 0
    for page in sorted(site.glob("*.html")):
        h = page.read_text(errors="ignore")
        if OLD_JS in h:
            page.write_text(h.replace("/js/" + OLD_JS, "/js/" + NEW_JS))
            pages += 1
    op = site / "operator.html"
    h = op.read_text()
    h = sub_once(h, OP_HTML_OLD, OP_HTML_NEW, "operator.html")
    op.write_text(h)
    return pages

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True)
    a = ap.parse_args(); root = pathlib.Path(a.root)
    lib = root / "netlify/functions/_lib"
    patch_products(lib / "products.js")
    patch_engine(lib / "engine.js")
    n = patch_client(root / "site")
    left = [p.name for p in (root / "site").glob("*.html") if OLD_JS in p.read_text(errors="ignore")]
    if left:
        sys.exit(f"harden_listing_escape: pages still on {OLD_JS}: {left}")
    print(f"harden_listing_escape: OK (server products/engine patched; {NEW_JS}; {n} pages repointed this run)")

if __name__ == "__main__":
    main()
