#!/usr/bin/env python3
"""BSV recipe: cubic polynomial joint path between two waypoints (zero end velocities).

Research / education / simulation only. Not a real-time motion planner.

Input : q0,q1 radians (default 0.0,1.2), duration s (default 1.0), dt s (default 0.02).
Output: cubic_path.csv with t_s,q,qd,qdd.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

def main(q0="0.0", q1="1.2", T="1.0", dt="0.02"):
    q0, q1, T, dt = float(q0), float(q1), float(T), float(dt)
    if T <= 0 or dt <= 0:
        raise SystemExit("T and dt must be positive")
    # q(t)=a0+a1 t+a2 t^2+a3 t^3 with q(0)=q0,q(T)=q1,qd(0)=qd(T)=0
    a0, a1 = q0, 0.0
    a2 = 3 * (q1 - q0) / (T * T)
    a3 = -2 * (q1 - q0) / (T * T * T)
    ts = np.arange(0.0, T + 1e-12, dt)
    rows = []
    for t in ts:
        q = a0 + a1 * t + a2 * t * t + a3 * t * t * t
        qd = a1 + 2 * a2 * t + 3 * a3 * t * t
        qdd = 2 * a2 + 6 * a3 * t
        rows.append({"t_s": float(t), "q": float(q), "qd": float(qd), "qdd": float(qdd)})
    with open("cubic_path.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t_s", "q", "qd", "qdd"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} cubic samples q0={q0}→q1={q1} T={T}s -> cubic_path.csv")

if __name__ == "__main__":
    main(*sys.argv[1:5])
