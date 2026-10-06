#!/usr/bin/env node
// Regression: user-supplied listing fields stay inert on every surface (server + client + email + digest).
// Usage: node scripts/site/test_listing_escape.js <stage root>   (root holds site/ and netlify/)
"use strict";
process.env.COMMERCE_TEST = "1";
const path = require("path"), fs = require("fs"), vm = require("vm");
const root = path.resolve(process.argv[2] || ".");
const lib = path.join(root, "netlify/functions/_lib");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const PWN = 'PWNMARKER-OPS16 console.log("pwn:botshelfvampire.com")';
const TAG = '<img src=x onerror=alert(1)>"\'><script>alert(1)</script>';
const BAD_URLS = ["javascript:alert(1)", "JaVaScRiPt:alert(1)", " javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "//evil.example/x", "https://x.com/a\"onmouseover=alert(1)", "https://evil.example/x"];

(async () => {
  const engine = require(path.join(lib, "engine.js"));
  const session = require(path.join(lib, "session.js"));
  const products = require(path.join(lib, "products.js"));
  const notifications = require(path.join(lib, "notifications.js"));
  const C = require(path.join(lib, "constants.js"));
  const J = (r) => JSON.parse(r.body || "{}");

  // server: safePublicXUrl
  ok(typeof products.safePublicXUrl === "function", "products.safePublicXUrl exported");
  BAD_URLS.forEach((u) => ok(products.safePublicXUrl(u) === "", "x url rejected: " + u));
  ["https://x.com/dagram_trader", "https://twitter.com/abc/status/1", "https://www.x.com/abc?s=1"].forEach((u) => ok(products.safePublicXUrl(u) === u, "x url kept: " + u));

  // seller with verified email + TRC20
  let u = await session.upsertUser({ email: "probe-seller@example.com", display_name: TAG, role: "seller" });
  u.email_verified = true; await session.putUser(u);
  const sid = (await session.createSession(u)).id;
  const w = await engine.invoke("POST", "/seller/wallet", { session_id: sid, body: { wallet_address: "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" } });
  ok(w.statusCode === 200, "wallet saved " + w.statusCode + " " + w.body);
  const ids = [];
  for (const title of [PWN, TAG]) {
    const r = await engine.invoke("POST", "/seller/listings", { session_id: sid, body: {
      title, listing_type: "PAID", product_type: C.PRODUCT_TYPES[0], price_usdt: "20", status: "SUBMITTED", rights_confirmed: true,
      short_description: "<svg onload=alert(1)>", description: TAG, runtime: '"><b>x</b>', show_x_publicly: true, public_x_url: "javascript:alert(1)",
      show_email_publicly: true, public_email: "probe-seller@example.com", prerequisites: [{ a: "<b>" }, TAG] } });
    const j = J(r); ok(r.statusCode === 200 && j.ok, "listing submitted " + r.body); ids.push(j.listing.id);
  }
  // draft with junk product_type
  const d = J(await engine.invoke("POST", "/seller/listings", { session_id: sid, body: { title: PWN, listing_type: "PAID", product_type: "<script>alert(1)</script>", status: "DRAFT" } }));
  ok(d.ok, "draft saved");
  // stored record: x url dropped, product_type token only, prerequisites strings
  const blobs = require(path.join(lib, "blobs.js"));
  const store = await blobs.getStore("listings");
  const rec0 = await blobs.getJSON(store, ids[0]);
  ok(rec0.public_x_url === "", "stored public_x_url dropped");
  ok(Array.isArray(rec0.prerequisites) && rec0.prerequisites.every((x) => typeof x === "string"), "prerequisites coerced to strings");
  const recD = await blobs.getJSON(store, d.listing.id);
  ok(!/[<>()]/.test(recD.product_type), "draft product_type token only: " + recD.product_type);
  // legacy record saved before the fix still cannot surface a javascript: link
  rec0.public_x_url = "javascript:alert(1)"; rec0.status = C.LISTING.PUBLISHED; await blobs.putJSON(store, ids[0], rec0);
  const pubView = products.publicListingView(rec0);
  ok(pubView && !pubView.public_x_url, "publicListingView drops legacy javascript: x url");
  ok(pubView && !/[<>]/.test(pubView.name + pubView.short_description + pubView.runtime), "public view text has no < >");
  const cat = J(await engine.invoke("GET", "/catalog/public"));
  const item = (cat.listings || []).find((x) => x.id === ids[0]);
  ok(item && !item.public_x_url && !/[<>]/.test(JSON.stringify([item.name, item.short_description, item.runtime])), "public catalog item inert");
  rec0.status = C.LISTING.SUBMITTED; delete rec0.public_x_url; await blobs.putJSON(store, ids[0], rec0);

  // operator reject (existing admin endpoint) -> SUSPENDED, absent from catalog, seller notice is text/plain
  for (const id of ids) {
    const r = J(await engine.invoke("POST", "/operator/listing", { admin: true, body: { listing_id: id, action: "reject", reason: "probe <b>x</b>" } }));
    ok(r.ok && r.status === C.LISTING.SUSPENDED, "operator reject " + id + " " + JSON.stringify(r));
  }
  const noAdmin = await engine.invoke("POST", "/operator/listing", { body: { listing_id: ids[0], action: "reject" } });
  ok(noAdmin.statusCode >= 400, "reject without admin secret refused " + noAdmin.statusCode);
  const cat2 = J(await engine.invoke("GET", "/catalog/public"));
  ok(!(cat2.listings || []).some((x) => ids.includes(x.id)), "rejected listings not public");
  const tpl = notifications.TEMPLATES || notifications.templates;
  if (tpl && tpl["seller.listing_rejected"]) {
    const m = tpl["seller.listing_rejected"]({ listing_name: TAG, reason_plain: "x" });
    ok(!/[\r\n]/.test(m.subject), "email subject single line");
  }
  const smtp = fs.readFileSync(path.join(lib, "smtp.js"), "utf8");
  ok(/Content-Type: text\/plain/.test(smtp) && !/text\/html/.test(smtp), "outgoing mail is text/plain only");
  ok(/replace\(\/\[\\r\\n\]\+\/g, " "\)/.test(smtp), "subject CR/LF stripped");
  // operator customer digest page renders with textContent only
  const opc = fs.readdirSync(path.join(root, "site/js")).filter((f) => /^operator-customers\.v\d+\.js$/.test(f)).sort().pop();
  const opcSrc = fs.readFileSync(path.join(root, "site/js", opc), "utf8");
  ok(!/innerHTML|insertAdjacentHTML|outerHTML|document\.write/.test(opcSrc), opc + " uses no HTML sinks");

  // client: commerce-client
  const files = fs.readdirSync(path.join(root, "site/js")).filter((f) => /^commerce-client\.v\d+\.js$/.test(f)).sort();
  const latest = files.pop();
  const src = fs.readFileSync(path.join(root, "site/js", latest), "utf8");
  const win = {}; const doc = { addEventListener() {}, getElementById() { return null; }, querySelector() { return null; }, querySelectorAll() { return []; } };
  vm.runInNewContext(src, { window: win, document: doc, localStorage: { getItem() { return ""; }, setItem() {}, removeItem() {} }, URLSearchParams, fetch: () => Promise.reject(new Error("x")), console });
  const R = win.BSVCommerce && win.BSVCommerce._render;
  ok(!!R, latest + " exposes _render");
  if (R) {
    ok(R.esc(TAG).indexOf("<") < 0 && R.esc("'\"").indexOf("'") < 0 && R.esc("'\"").indexOf('"') < 0, "esc escapes < > \" '");
    BAD_URLS.slice(0, 5).forEach((x) => ok(R.safeUrl(x) === "", "client safeUrl rejects " + x));
    ok(R.safeUrl("https://x.com/a") === "https://x.com/a" && R.safeUrl("listing.html?id=lst_1") === "listing.html?id=lst_1", "client safeUrl keeps https + relative");
    const card = R.cardHtml({ id: '"><script>alert(1)</script>', name: PWN + TAG, short_description: TAG, runtime: TAG, product_type: TAG, listing_type: "PAID", price_usdt: TAG, href: "javascript:alert(1)", public_x_url: "javascript:alert(1)", public_email: 'a@b.c"><script>' });
    ok(!/<(script|img|svg)\b/i.test(card) && !/href="\s*(javascript|data):/i.test(card) && !/"\s+on[a-z]+=/i.test(card), "card HTML inert: " + card.slice(0, 160));
    ok(card.indexOf("PWNMARKER-OPS16 console.log(&quot;pwn:botshelfvampire.com&quot;)") >= 0, "PWNMARKER name shown as text");
    const card2 = R.cardHtml({ id: "lst_ok", name: "ok", listing_type: "FREE", public_x_url: "https://x.com/dagram_trader", public_email: "s@example.com" });
    ok(/href="https:\/\/x\.com\/dagram_trader"/.test(card2) && /mailto:s@example\.com/.test(card2), "valid seller links still shown");
  }
  // every innerHTML/html()/table() sink in the client gets data only through esc()/safeUrl()
  const rawConcat = src.split("\n").filter((l) => /(innerHTML|html\(|table\()/.test(l) && /\+ ?(?:item|p|l|s|b|x|n|o|j|r)\.[a-z_]+/.test(l) && !/esc\(/.test(l));
  ok(rawConcat.length === 0, "no unescaped data concatenation into HTML sinks: " + rawConcat.join(" | "));
  // pages load the patched client, operator has the review box
  const site = path.join(root, "site");
  const stale = fs.readdirSync(site).filter((f) => f.endsWith(".html") && /commerce-client\.v20260912c\.js/.test(fs.readFileSync(path.join(site, f), "utf8")));
  ok(stale.length === 0, "no page loads the old commerce client: " + stale.join(","));
  const op = fs.readFileSync(path.join(site, "operator.html"), "utf8");
  ok(op.includes(latest) && op.includes('id="op-lst-reject"') && op.includes('id="op-lst-id"'), "operator listing review wired");
  console.log(`test_listing_escape: ${pass} passed, ${fail} failed (${latest})`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("test_listing_escape crashed:", e && e.stack || e); process.exit(1); });
