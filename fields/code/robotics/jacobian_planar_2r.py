#!/usr/bin/env python3
"""BSV recipe: planar 2R geometric Jacobian + manipulability along a joint sweep.

Research / education / simulation only. Not a safety-rated controller.

Input : L1,L2 meters (default 0.12,0.10), q1 start/stop/step rad (default 0,1.57,0.1), q2 fixed (default 0.8).
Output: jacobian_2r.csv with q1,q2,x,y,det_j,manipulability,sigma_min,sigma_max.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

def fk(q1, q2, L1, L2):
    x = L1 * np.cos(q1) + L2 * np.cos(q1 + q2)
    y = L1 * np.sin(q1) + L2 * np.sin(q1 + q2)
    return float(x), float(y)

def J(q1, q2, L1, L2):
    s1, c1 = np.sin(q1), np.cos(q1)
    s12, c12 = np.sin(q1 + q2), np.cos(q1 + q2)
    return np.array([
        [-L1 * s1 - L2 * s12, -L2 * s12],
        [L1 * c1 + L2 * c12, L2 * c12],
    ], dtype=float)

def main(L1="0.12", L2="0.10", q1_start="0", q1_stop="1.57", q1_step="0.1", q2="0.8"):
    L1, L2 = float(L1), float(L2)
    q2 = float(q2)
    qs = np.arange(float(q1_start), float(q1_stop) + 1e-12, float(q1_step))
    rows = []
    for q1 in qs:
        Jac = J(q1, q2, L1, L2)
        x, y = fk(q1, q2, L1, L2)
        det = float(np.linalg.det(Jac))
        # Yoshikawa manipulability sqrt(det(J J^T))
        w = float(np.sqrt(max(0.0, np.linalg.det(Jac @ Jac.T))))
        s = np.linalg.svd(Jac, compute_uv=False)
        rows.append({
            "q1_rad": q1, "q2_rad": q2, "x_m": x, "y_m": y,
            "det_j": det, "manipulability": w,
            "sigma_min": float(s.min()), "sigma_max": float(s.max()),
        })
    with open("jacobian_2r.csv", "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wri.writeheader(); wri.writerows(rows)
    print(f"wrote {len(rows)} Jacobian samples -> jacobian_2r.csv (min manip={min(r['manipulability'] for r in rows):.4f})")

if __name__ == "__main__":
    main(*sys.argv[1:7])
