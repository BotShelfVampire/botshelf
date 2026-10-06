#!/usr/bin/env python3
"""BSV recipe: PennyLane 2-qubit Ising — ⟨Z⊗Z⟩ after RX on both wires vs analytic.

Research / education only. default.qubit — not hardware.
Input : comma-separated theta pairs "a|b" (default 0.3|0.5,0.8|0.2,1.2|1.0).
Output: ising_zz.csv with theta_a, theta_b, expval_zz, analytic, abs_err.
Original BSV code, MIT. Library: PennyLane (Apache-2.0).
"""
import csv, math, sys
import pennylane as qml

def main(pairs="0.3|0.5,0.8|0.2,1.2|1.0"):
    items = []
    for part in (pairs or "").split(","):
        part = part.strip()
        if not part:
            continue
        a, b = part.split("|")
        items.append((float(a), float(b)))
    if not items:
        raise SystemExit("need at least one a|b pair")
    dev = qml.device("default.qubit", wires=2)

    @qml.qnode(dev)
    def circ(ta, tb):
        qml.RX(ta, wires=0)
        qml.RX(tb, wires=1)
        return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

    rows = []
    for ta, tb in items:
        val = float(circ(ta, tb))
        # ⟨Z⊗Z⟩ on RX(a)|0⟩⊗RX(b)|0⟩ = cos(a)cos(b)
        ana = math.cos(ta) * math.cos(tb)
        rows.append({"theta_a": ta, "theta_b": tb, "expval_zz": val, "analytic": ana, "abs_err": abs(val - ana)})
    with open("ising_zz.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["theta_a", "theta_b", "expval_zz", "analytic", "abs_err"])
        w.writeheader(); w.writerows(rows)
    max_err = max(r["abs_err"] for r in rows)
    print(f"wrote {len(rows)} Ising ZZ points, max |err|={max_err:.2e} -> ising_zz.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
