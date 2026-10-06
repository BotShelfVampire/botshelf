#!/usr/bin/env python3
"""BSV recipe: sample planar 2R manipulability (|det J|) across a joint grid.

Research / education / simulation only.
Input : L1,L2 (default 0.12 0.10), grid n (default 24).
Output: manip_ellipse.csv with q1,q2,detJ,manip.
Original BSV code, MIT. Dependency: math (stdlib).
"""
import csv, math, sys

def main(L1="0.12", L2="0.10", n="24"):
    L1, L2, n = float(L1), float(L2), int(n)
    rows = []
    for i in range(n):
        for j in range(n):
            q1 = -math.pi + 2 * math.pi * i / max(n - 1, 1)
            q2 = -math.pi + 2 * math.pi * j / max(n - 1, 1)
            s1, c1 = math.sin(q1), math.cos(q1)
            s12, c12 = math.sin(q1 + q2), math.cos(q1 + q2)
            # J = [[-L1 s1 - L2 s12, -L2 s12],[L1 c1 + L2 c12, L2 c12]]
            det = (-L1 * s1 - L2 * s12) * (L2 * c12) - (-L2 * s12) * (L1 * c1 + L2 * c12)
            rows.append({"q1": q1, "q2": q2, "detJ": det, "manip": abs(det)})
    with open("manip_ellipse.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["q1", "q2", "detJ", "manip"])
        w.writeheader(); w.writerows(rows)
    best = max(rows, key=lambda r: r["manip"])
    print(f"wrote {len(rows)} configs max|detJ|={best['manip']:.5f} at q=({best['q1']:.3f},{best['q2']:.3f}) -> manip_ellipse.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
