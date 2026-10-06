#!/usr/bin/env python3
"""BSV recipe: PennyLane RX(θ) circuit — ⟨Z⟩ vs analytic cos(θ).

Research / education only. Default.qubit simulator — not hardware.
Input : comma-separated angles in radians (default 0,0.5,1,1.5,2,2.5,3).
Output: rx_expectation.csv with theta, expval_z, analytic_cos, abs_err.
Original BSV code, MIT. Library: PennyLane (Apache-2.0).
"""
import csv, math, sys
import pennylane as qml
from pennylane import numpy as np

def main(angles="0,0.5,1,1.5,2,2.5,3"):
    thetas = [float(x) for x in (angles or "0").split(",") if x.strip() != ""]
    dev = qml.device("default.qubit", wires=1)

    @qml.qnode(dev)
    def circ(theta):
        qml.RX(theta, wires=0)
        return qml.expval(qml.PauliZ(0))

    rows = []
    for th in thetas:
        val = float(circ(th))
        ana = math.cos(th)
        rows.append({"theta": th, "expval_z": val, "analytic_cos": ana, "abs_err": abs(val - ana)})
    with open("rx_expectation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["theta", "expval_z", "analytic_cos", "abs_err"])
        w.writeheader(); w.writerows(rows)
    max_err = max(r["abs_err"] for r in rows)
    print(f"wrote {len(rows)} RX⟨Z⟩ points, max |err|={max_err:.2e} -> rx_expectation.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
