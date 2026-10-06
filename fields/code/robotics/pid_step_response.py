#!/usr/bin/env python3
"""BSV recipe: discrete PID step response on a 1st-order plant.

Research / education / simulation only — not a real controller or safety case.
Input : optional Kp,Ki,Kd,plant_tau (defaults 1.2 0.4 0.05 0.8), steps (default 80).
Output: pid_step.csv with t, r, y, u.
Original BSV code, MIT. Dependency: none (stdlib).
"""
import csv, sys

def main(kp="1.2", ki="0.4", kd="0.05", tau="0.8", steps="80"):
    Kp, Ki, Kd, tau, N = float(kp), float(ki), float(kd), float(tau), int(steps)
    dt = 0.05
    y = 0.0; integ = 0.0; prev_e = 0.0; r = 1.0
    rows = []
    a = dt / (tau + dt)  # plant y += a*(u-y)
    for k in range(N):
        e = r - y
        integ += e * dt
        deriv = (e - prev_e) / dt
        u = Kp * e + Ki * integ + Kd * deriv
        y = y + a * (u - y)
        prev_e = e
        rows.append({"t": round(k * dt, 4), "r": r, "y": y, "u": u, "e": e})
    with open("pid_step.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t", "r", "y", "u", "e"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} PID samples final_y={y:.4f} -> pid_step.csv")

if __name__ == "__main__":
    main(*sys.argv[1:6])
