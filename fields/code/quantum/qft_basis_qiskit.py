#!/usr/bin/env python3
"""BSV recipe: 3-qubit QFT on a computational basis state (Qiskit Aer).

Prepare |k⟩, apply QFT, measure. Education only — illustrates frequency peaks, not Shor.
Input : basis integer k in 0..7 (default 3), shots (default 4000).
Output: qft_basis.csv with outcome counts and prepared_k.
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.library import QFTGate

def main(k="3", shots="4000"):
    k = int(k); shots = int(shots)
    if not (0 <= k <= 7):
        raise SystemExit("k must be 0..7")
    n = 3
    qc = QuantumCircuit(n, n)
    for i in range(n):
        if (k >> i) & 1:
            qc.x(i)
    qc.append(QFTGate(n), range(n))
    qc.measure(range(n), range(n))
    sim = AerSimulator(seed_simulator=17)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    with open("qft_basis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["outcome", "count", "share"])
        for outcome in sorted(counts):
            w.writerow([outcome, counts[outcome], f"{counts[outcome]/shots:.4f}"])
        w.writerow(["prepared_k", k, ""])
        w.writerow(["shots", shots, ""])
    top = max(counts, key=counts.get)
    print(f"|{k}> --QFT--> top={top} share={counts[top]/shots:.3f} ({len(counts)} bins) -> qft_basis.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
