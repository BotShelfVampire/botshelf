#!/usr/bin/env python3
"""BSV recipe: resample a joint-space trajectory CSV onto a uniform time grid.

Research / education / simulation only. Synthetic default file is labeled example-row.

Input : path to CSV with columns t_s,q1,q2,... (default: write labeled sample), dt seconds (default 0.02).
Output: traj_resampled.csv
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

SAMPLE = """t_s,q1,q2,note
0.00,0.0,0.0,example-row
0.10,0.2,0.1,example-row
0.25,0.5,0.4,example-row
0.40,0.7,0.6,example-row
0.55,0.6,0.5,example-row
"""

def main(path=None, dt="0.02"):
    if not path:
        path = "traj_sample_labeled.csv"
        open(path, "w", encoding="utf-8").write(SAMPLE)
        print("wrote labeled synthetic sample:", path)
    rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    if len(rows) < 2:
        raise SystemExit("need at least 2 rows")
    cols = [c for c in rows[0].keys() if c != "note"]
    if "t_s" not in cols:
        raise SystemExit("CSV must include t_s")
    joint_cols = [c for c in cols if c != "t_s"]
    t = np.array([float(r["t_s"]) for r in rows], dtype=float)
    Q = np.array([[float(r[c]) for c in joint_cols] for r in rows], dtype=float)
    dt = float(dt)
    t_new = np.arange(t[0], t[-1] + 1e-12, dt)
    Qn = np.vstack([np.interp(t_new, t, Q[:, j]) for j in range(Q.shape[1])]).T
    with open("traj_resampled.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_s", *joint_cols])
        for i, ti in enumerate(t_new):
            w.writerow([f"{ti:.6f}", *[f"{v:.8f}" for v in Qn[i]]])
    print(f"resampled {len(rows)} -> {len(t_new)} rows at dt={dt}s -> traj_resampled.csv")

if __name__ == "__main__":
    main(*sys.argv[1:])
