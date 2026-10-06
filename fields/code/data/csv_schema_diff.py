#!/usr/bin/env python3
"""BSV recipe: diff two CSV schemas — shared, only-left, only-right columns + type guesses.

Input : two CSV paths (default: writes two labeled synthetic samples that intentionally differ).
Output: schema_diff.csv + schema_diff.md
Original BSV code, MIT. Synthetic rows are labeled examples, not customer data.
"""
import csv, os, sys
from collections import OrderedDict

A = """id,city,temp_c,note
1,Tokyo,22.1,example-row
2,Osaka,19.0,example-row
"""
B = """id,city,humidity_pct,note,sensor
1,Tokyo,55,example-row,demo
2,Kyoto,60,example-row,demo
"""

def guess(vals):
    filled = [v.strip() for v in vals if v is not None and str(v).strip() != ""]
    if not filled:
        return "empty"
    try:
        for v in filled:
            float(v)
        return "numeric"
    except Exception:
        return "text"

def cols(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    if not rows:
        return OrderedDict()
    out = OrderedDict()
    for c in rows[0].keys():
        out[c] = guess([r.get(c, "") for r in rows])
    return out

def main(left=None, right=None):
    if not left or not right:
        left, right = "sample_a_labeled.csv", "sample_b_labeled.csv"
        open(left, "w", encoding="utf-8").write(A)
        open(right, "w", encoding="utf-8").write(B)
        print("wrote labeled synthetic pair:", left, right)
    la, rb = cols(left), cols(right)
    sa, sb = set(la), set(rb)
    rows = []
    for c in list(la) + [c for c in rb if c not in la]:
        side = "both" if c in sa and c in sb else ("left_only" if c in sa else "right_only")
        rows.append({"column": c, "side": side, "left_type": la.get(c, ""), "right_type": rb.get(c, ""),
                     "type_match": str(la.get(c) == rb.get(c)).lower() if side == "both" else ""})
    with open("schema_diff.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["column", "side", "left_type", "right_type", "type_match"])
        w.writeheader(); w.writerows(rows)
    lines = [f"# Schema diff `{left}` vs `{right}`", "",
             f"Shared: {len(sa & sb)}  Left-only: {len(sa - sb)}  Right-only: {len(sb - sa)}", "",
             "Synthetic practice files stay labeled; do not treat sample numbers as live metrics.", ""]
    for r in rows:
        lines.append(f"- `{r['column']}` · {r['side']} · L={r['left_type'] or '-'} R={r['right_type'] or '-'}")
    open("schema_diff.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"diff {len(rows)} columns -> schema_diff.csv, schema_diff.md")

if __name__ == "__main__":
    main(*(sys.argv[1:3] or []))
