#!/usr/bin/env python3
"""Free-team pages carry "Last checked D (JST). Recheck by R." Never move D or R without a real re-run.
This pass (idempotent) makes an overdue recheck visible instead of silently stale:
  - the line becomes an EN + JA pair, each with a .recheck-overdue note (data-recheck-by=R);
  - the note is shown when the build date (JST) is after R, and /js/recheck-status.v20261007.js re-evaluates it
    in the browser so a page built before R still flips to overdue on time;
  - the qc-stamp blocks get the same note.
--check verifies the result (used by tests)."""
import argparse, datetime as dt, pathlib, re, sys

JS_NAME = "recheck-status.v20261007.js"
JS = """(function () {
  "use strict";
  // Shows .recheck-overdue notes once today's JST date is after data-recheck-by (YYYY-MM-DD). No dates are changed.
  function todayJst() { return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); }
  function run() {
    var t = todayJst();
    document.querySelectorAll(".recheck-overdue[data-recheck-by]").forEach(function (n) {
      var by = n.getAttribute("data-recheck-by") || "";
      if (/^\\d{4}-\\d{2}-\\d{2}$/.test(by)) n.hidden = !(t > by);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
"""
LINE = re.compile(r'<p><strong>(\d{4}-\d{2}-\d{2})</strong> \(JST\)\. Recheck by (\d{4}-\d{2}-\d{2})\.</p>')
STAMP_EN = re.compile(r'(<pre class="qc-stamp" data-lang-show="en">Last checked: (\d{4}-\d{2}-\d{2})\n)')
STAMP_JA = re.compile(r'(<pre class="qc-stamp" data-lang-show="ja" hidden>最終確認日: (\d{4}-\d{2}-\d{2})\n)')

def note_en(d, r, hid):
    return f'<span class="recheck-overdue" data-recheck-by="{r}"{hid}> <strong>Recheck overdue:</strong> not re-run since {d}. Treat this page as unverified until it is re-run.</span>'
def note_ja(d, r, hid):
    return f'<span class="recheck-overdue" data-recheck-by="{r}"{hid}> <strong>再確認の期限切れ：</strong>{d} 以降は再実行していません。再実行するまでは未確認として扱ってください。</span>'

def apply(t, today):
    m = LINE.search(t)
    if not m:
        return t, None
    d, r = m.group(1), m.group(2)
    hid = "" if today > r else " hidden"
    pair = (f'<p data-lang-show="en"><strong>{d}</strong> (JST). Recheck by {r}.{note_en(d, r, hid)}</p>\n'
            f' <p data-lang-show="ja" hidden><strong>{d}</strong>（日本時間）。再確認の期限: {r}。{note_ja(d, r, hid)}</p>')
    t = t[:m.start()] + pair + t[m.end():]
    t = STAMP_EN.sub(lambda x: x.group(1) + f'<span class="recheck-overdue" data-recheck-by="{r}"{hid}>Recheck: overdue (due {r})\n</span>', t, count=1)
    t = STAMP_JA.sub(lambda x: x.group(1) + f'<span class="recheck-overdue" data-recheck-by="{r}"{hid}>再確認: 期限切れ（期限 {r}）\n</span>', t, count=1)
    tag = f'<script src="/js/{JS_NAME}" defer></script>'
    if tag not in t:
        t = t.replace("</body>", tag + "\n</body>", 1)
    return t, (d, r, hid == "")

def refresh_hidden(t, today):
    # rebuilds keep the notes but recompute hidden from the build date
    def fix(x):
        r = x.group(2); return f'<span class="recheck-overdue" data-recheck-by="{r}"' + ("" if today > r else " hidden") + ">"
    return re.sub(r'<span class="recheck-overdue" data-recheck-by="((\d{4}-\d{2}-\d{2}))"(?: hidden)?>', fix, t)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); ap.add_argument("--check", action="store_true")
    ap.add_argument("--today", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d"))
    a = ap.parse_args(); site = pathlib.Path(a.site)
    pages = [p for p in sorted(site.glob("*.html")) if "Recheck by 20" in p.read_text(errors="ignore")]
    fails, rows = [], []
    for p in pages:
        t = p.read_text()
        if not a.check:
            t2, info = apply(t, a.today)
            t2 = refresh_hidden(t2, a.today)
            if t2 != t: p.write_text(t2)
            t = t2
        spans = re.findall(r'<span class="recheck-overdue" data-recheck-by="(\d{4}-\d{2}-\d{2})"( hidden)?>', t)
        dates = re.findall(r'Recheck by (\d{4}-\d{2}-\d{2})', t)
        if LINE.search(t): fails.append(f"{p.name}: unconverted recheck line")
        if len(spans) < 2 or len(set(s[0] for s in spans)) != 1 or set(dates) != {spans[0][0]}: fails.append(f"{p.name}: notes {spans} vs dates {dates}")
        elif any((s[1] == " hidden") != (a.today <= s[0]) for s in spans): fails.append(f"{p.name}: hidden state wrong for {a.today}")
        if f'/js/{JS_NAME}' not in t: fails.append(f"{p.name}: status script missing")
        if t.count('data-lang-show="en"') != t.count('data-lang-show="ja"'): fails.append(f"{p.name}: en/ja not paired")
        if spans: rows.append({"page": p.name, "recheck_by": spans[0][0], "overdue": spans[0][1] == ""})
    js = site / "js" / JS_NAME
    if not a.check: js.write_text(JS)
    if not js.exists(): fails.append("status script file missing")
    print({"test" if a.check else "pass": "recheck_overdue", "today_jst": a.today, "pages": rows, "failures": len(fails), "fail": fails})
    if fails: sys.exit(1)

if __name__ == "__main__":
    main()
