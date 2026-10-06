#!/usr/bin/env python3
"""Deny-list disposable/probe email domains at the account gate (idempotent).

Blocks registration, OTP, session issue/load, and any upsertUser for:
  - entire domain uberip.com
  - explicit address pwnbv16@uberip.com
No auth redesign: same OTP/session flow; blocked emails get 403 email_blocked.
Does not change payment, pricing, wallets, or entitlement logic.
"""
import argparse, pathlib, sys

IDENTITY_MARK = "function isBlockedEmail"
IDENTITY_BLOCK = r'''
// Probe / disposable domains and addresses refused at every account gate (owner 2026-10-07).
var BLOCKED_EMAIL_DOMAINS = ["uberip.com"];
var BLOCKED_EMAILS = ["pwnbv16@uberip.com"];

function isBlockedEmail(email) {
  var n = String(email || "").trim().toLowerCase();
  if (!n) return false;
  if (BLOCKED_EMAILS.indexOf(n) >= 0) return true;
  var at = n.lastIndexOf("@");
  if (at < 0) return false;
  return BLOCKED_EMAIL_DOMAINS.indexOf(n.slice(at + 1)) >= 0;
}

function assertEmailAllowed(email) {
  var n = normalizeEmail(email);
  if (!n) {
    var err = new Error("invalid_email");
    err.code = "invalid_email";
    throw err;
  }
  if (isBlockedEmail(n)) {
    var e2 = new Error("email_blocked");
    e2.code = "email_blocked";
    e2.status = 403;
    throw e2;
  }
  return n;
}

'''

def sub_once(t, old, new, label):
    if new in t or IDENTITY_MARK in t and label.startswith("identity"):
        if IDENTITY_MARK in t and label.startswith("identity") and "assertEmailAllowed" in t:
            return t
    if new.strip() and new in t:
        return t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"block_probe_emails: {label}: expected 1 match, got {n}")
    return t.replace(old, new, 1)

def patch_identity(p):
    t = p.read_text()
    if "isBlockedEmail: isBlockedEmail" in t and "uberip.com" in t:
        return False
    if "function isBlockedEmail" in t:
        raise SystemExit("block_probe_emails: identity partial patch — restore and retry")
    needle = "function emailId(email) {"
    if t.count(needle) != 1:
        raise SystemExit("block_probe_emails: emailId anchor count=%d" % t.count(needle))
    t = t.replace(needle, IDENTITY_BLOCK + needle, 1)
    exp_old = "  normalizeEmail: normalizeEmail,\n  emailId: emailId,"
    exp_new = "  normalizeEmail: normalizeEmail,\n  isBlockedEmail: isBlockedEmail,\n  assertEmailAllowed: assertEmailAllowed,\n  emailId: emailId,"
    if exp_old not in t:
        raise SystemExit("block_probe_emails: identity exports anchor missing")
    t = t.replace(exp_old, exp_new, 1)
    p.write_text(t)
    return True

def patch_session(p):
    t = p.read_text(); orig = t
    # upsertUser: replace normalize+invalid with assertEmailAllowed
    a = """  var email = identity.normalizeEmail(fields.email);
  if (!email) {
    var err = new Error("invalid_email");
    err.code = "invalid_email";
    throw err;
  }"""
    b = """  var email = identity.assertEmailAllowed(fields.email);"""
    if a in t:
        t = t.replace(a, b, 1)
    elif "assertEmailAllowed(fields.email)" not in t:
        raise SystemExit("block_probe_emails: session upsertUser anchor missing")
    # createSession: block before issuing
    if "identity.assertEmailAllowed(user && user.email)" not in t and "identity.assertEmailAllowed(user.email)" not in t:
        old = "async function createSession(user, meta) {\n  var secret = sessionSecret();"
        new = "async function createSession(user, meta) {\n  identity.assertEmailAllowed(user && user.email);\n  var secret = sessionSecret();"
        if old not in t: raise SystemExit("block_probe_emails: createSession anchor missing")
        t = t.replace(old, new, 1)
    # loadSession: refuse blocked / keep REVOKED
    old = "  if (!user || user.status === \"REVOKED\") return null;"
    new = "  if (!user || user.status === \"REVOKED\" || identity.isBlockedEmail(user.email)) return null;"
    if "isBlockedEmail(user.email)" not in t:
        if old not in t: raise SystemExit("block_probe_emails: loadSession anchor missing")
        t = t.replace(old, new, 1)
    if t != orig:
        p.write_text(t); return True
    return False

def patch_email_verify(p):
    t = p.read_text(); orig = t
    for fn, anchor in (
        ("createChallenge", "async function createChallenge(email, meta) {\n  var n = identity.normalizeEmail(email);\n  if (!n) {\n    var err = new Error(\"invalid_email\");\n    err.code = \"invalid_email\";\n    throw err;\n  }"),
        ("verifyChallenge", None),
    ):
        pass
    a = """async function createChallenge(email, meta) {
  var n = identity.normalizeEmail(email);
  if (!n) {
    var err = new Error("invalid_email");
    err.code = "invalid_email";
    throw err;
  }"""
    b = """async function createChallenge(email, meta) {
  var n = identity.assertEmailAllowed(email);"""
    if a in t:
        t = t.replace(a, b, 1)
    elif "assertEmailAllowed(email)" not in t.split("createChallenge")[1][:200]:
        # already patched or different shape
        if "assertEmailAllowed(email)" not in t:
            raise SystemExit("block_probe_emails: createChallenge anchor missing")
    # verifyChallenge: after normalize, assert
    if "async function verifyChallenge(email, code) {\n  var n = identity.assertEmailAllowed(email);" not in t:
        old = "async function verifyChallenge(email, code) {\n  var n = identity.normalizeEmail(email);"
        new = "async function verifyChallenge(email, code) {\n  var n = identity.assertEmailAllowed(email);"
        if old not in t:
            if "assertEmailAllowed(email)" in t: pass
            else: raise SystemExit("block_probe_emails: verifyChallenge anchor missing")
        else:
            t = t.replace(old, new, 1)
    if t != orig:
        p.write_text(t); return True
    return False

def patch_engine(p):
    """Early deny on register/session/verify before any side effects."""
    t = p.read_text(); orig = t
    fold = 'code === "unauthorized" ? 401 : code === "admin-unconfigured"'
    fnew = 'code === "unauthorized" ? 401 : code === "email_blocked" ? 403 : code === "admin-unconfigured"'
    if 'email_blocked" ? 403' not in t and fold in t:
        t = t.replace(fold, fnew, 1)

    # After each `var email = identity.normalizeEmail(...); if (!email) throw err("invalid_email");`
    # add assert — but assertEmailAllowed already throws invalid_email / email_blocked.
    # Replace the three account entry points.
    old = '  var email = identity.normalizeEmail(body.email);\n  if (!email) throw err("invalid_email");'
    new = '  var email = identity.assertEmailAllowed(body.email);'
    if t.count(old) < 1 and "assertEmailAllowed(body.email)" not in t:
        raise SystemExit(f"block_probe_emails: engine email anchors missing (found {t.count(old)})")
    if old in t:
        t = t.replace(old, new)  # all occurrences in register/session/verify
    if t != orig:
        p.write_text(t); return True
    return False

def check(root):
    lib = root / "netlify/functions/_lib"
    fails = []
    idt = (lib / "identity.js").read_text()
    for needle in ("uberip.com", "pwnbv16@uberip.com", "isBlockedEmail", "assertEmailAllowed", "email_blocked"):
        if needle not in idt: fails.append(f"identity missing {needle}")
    sess = (lib / "session.js").read_text()
    for needle in ("assertEmailAllowed(fields.email)", "assertEmailAllowed(user && user.email)", "isBlockedEmail(user.email)"):
        if needle not in sess: fails.append(f"session missing {needle}")
    ev = (lib / "emailVerify.js").read_text()
    if ev.count("assertEmailAllowed(email)") < 2: fails.append("emailVerify needs assert on create+verify")
    eng = (lib / "engine.js").read_text()
    if "assertEmailAllowed(body.email)" not in eng: fails.append("engine missing assertEmailAllowed")
    # ensure legacy normalize-only on those paths is gone for account entry
    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    lib = root / "netlify/functions/_lib"
    if a.check:
        fails = check(root)
        print({"test": "block_probe_emails", "failures": len(fails), "fail": fails})
        sys.exit(1 if fails else 0)
    ch = {
        "identity": patch_identity(lib / "identity.js"),
        "session": patch_session(lib / "session.js"),
        "emailVerify": patch_email_verify(lib / "emailVerify.js"),
        "engine": patch_engine(lib / "engine.js"),
    }
    fails = check(root)
    print({"pass": "block_probe_emails", "changed": ch, "failures": len(fails), "fail": fails})
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
