#!/usr/bin/env python3
"""BSV recipe: sample a planar 2-link arm workspace and solve elbow-down IK.

Research / education / simulation only.

Input : L1, L2 in meters (default 0.12,0.10), grid half-extent mm (default 200), step mm (default 10).
Output: ik_workspace.csv with x_mm,y_mm,reachable,q1_rad,q2_rad,err_mm.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

def ik(x, y, L1, L2):
    r2 = x * x + y * y
    c2 = (r2 - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(c2) > 1.0:
        return None
    q2 = float(np.arccos(np.clip(c2, -1, 1)))
    q1 = float(np.arctan2(y, x) - np.arctan2(L2 * np.sin(q2), L1 + L2 * np.cos(q2)))
    return q1, q2

def fk(q1, q2, L1, L2):
    x = L1 * np.cos(q1) + L2 * np.cos(q1 + q2)
    y = L1 * np.sin(q1) + L2 * np.sin(q1 + q2)
    return float(x), float(y)

def main(L1="0.12", L2="0.10", half_mm="200", step_mm="10"):
    L1, L2 = float(L1), float(L2)
    half, step = float(half_mm) / 1000.0, float(step_mm) / 1000.0
    xs = np.arange(-half, half + 1e-9, step)
    ys = np.arange(-half, half + 1e-9, step)
    rows, ok = [], 0
    for x in xs:
        for y in ys:
            sol = ik(x, y, L1, L2)
            if sol is None:
                rows.append([x * 1000, y * 1000, 0, "", "", ""])
                continue
            q1, q2 = sol
            xr, yr = fk(q1, q2, L1, L2)
            err = ((xr - x) ** 2 + (yr - y) ** 2) ** 0.5 * 1000
            rows.append([x * 1000, y * 1000, 1, q1, q2, err])
            ok += 1
    with open("ik_workspace.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x_mm", "y_mm", "reachable", "q1_rad", "q2_rad", "fk_err_mm"])
        w.writerows(rows)
    print(f"grid {len(xs)}×{len(ys)} = {len(rows)} cells, reachable {ok} -> ik_workspace.csv")

if __name__ == "__main__":
    main(*sys.argv[1:])
