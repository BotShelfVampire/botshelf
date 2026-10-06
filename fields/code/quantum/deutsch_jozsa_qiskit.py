#!/usr/bin/env python3
"""BSV recipe: Deutsch–Jozsa — constant vs balanced with one oracle query (Qiskit Aer).

Research / education only. Simulator only — not a hardware-advantage claim.
Input : oracle kind constant0|constant1|balanced (default balanced), shots (default 2000).
Output: dj_result.csv with per-outcome counts, oracle_kind, classified, zero_share.
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def apply_oracle(qc, kind, n=3):
    if kind == "constant0":
        return
    if kind == "constant1":
        qc.x(n); return
    if kind == "balanced":
        for i in range(n):
            qc.cx(i, n)
        return
    raise SystemExit(f"unknown oracle kind {kind!r}")

def main(kind="balanced", shots="2000"):
    kind = (kind or "balanced").strip()
    shots = int(shots)
    n = 3
    qc = QuantumCircuit(n + 1, n)
    qc.x(n); qc.h(n)
    qc.h(range(n))
    apply_oracle(qc, kind, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    sim = AerSimulator(seed_simulator=7)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    zero_key = "0" * n
    zero = counts.get(zero_key, 0)
    classified = "constant" if zero / shots >= 0.5 else "balanced"
    with open("dj_result.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["outcome", "count"])
        for k in sorted(counts):
            w.writerow([k, counts[k]])
        w.writerow(["oracle_kind", kind])
        w.writerow(["classified", classified])
        w.writerow(["zero_share", f"{zero / shots:.4f}"])
    print(f"oracle={kind} classified={classified} zero_share={zero/shots:.3f} -> dj_result.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
