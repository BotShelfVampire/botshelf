#!/usr/bin/env python3
"""BSV recipe: trapezoidal velocity profile for a scalar joint move.

Research / education / simulation only — not a motion controller.
Input : distance, vmax, amax (defaults 1.0 0.5 1.0), dt (default 0.01).
Output: trap_profile.csv with t, s, v, a.
Original BSV code, MIT. Dependency: none.
"""
import csv, math, sys

def main(distance="1.0", vmax="0.5", amax="1.0", dt="0.01"):
    D, vmax, amax, dt = abs(float(distance)), abs(float(vmax)), abs(float(amax)), float(dt)
    # time to vmax
    t_acc = vmax / amax
    d_acc = 0.5 * amax * t_acc ** 2
    if 2 * d_acc >= D:  # triangle
        t_acc = math.sqrt(D / amax)
        t_flat = 0.0
        vmax = amax * t_acc
    else:
        t_flat = (D - 2 * d_acc) / vmax
    t_total = 2 * t_acc + t_flat
    rows = []
    t = 0.0
    while t <= t_total + 1e-12:
        if t < t_acc:
            a = amax; v = amax * t; s = 0.5 * amax * t ** 2
        elif t < t_acc + t_flat:
            a = 0.0; v = vmax; s = d_acc + vmax * (t - t_acc)
        else:
            tau = t - (t_acc + t_flat)
            a = -amax; v = vmax - amax * tau; s = D - 0.5 * amax * (t_acc - tau) ** 2
            # cleaner: s = d_acc + vmax*t_flat + vmax*tau - 0.5*amax*tau**2
            s = d_acc + vmax * t_flat + vmax * tau - 0.5 * amax * tau ** 2
        rows.append({"t": round(t, 5), "s": s, "v": v, "a": a})
        t += dt
    with open("trap_profile.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t", "s", "v", "a"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} samples t_total={t_total:.4f}s vmax_used={vmax:.4f} -> trap_profile.csv")

if __name__ == "__main__":
    main(*sys.argv[1:5])
