#!/usr/bin/env python3
"""BSV recipe: prepare a 3-qubit GHZ state and measure correlations (Qiskit Aer).

Research / education only. Simulator only.
Input : shots (default 4000).
Output: ghz_counts.csv with outcome counts and a printed GHZ-correlated share (000+111).
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def main(shots="4000"):
    shots = int(shots)
    qc = QuantumCircuit(3, 3)
    qc.h(0); qc.cx(0, 1); qc.cx(0, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    sim = AerSimulator(seed_simulator=7)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    with open("ghz_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["outcome", "count"])
        for k in ("000", "001", "010", "011", "100", "101", "110", "111"):
            w.writerow([k, counts.get(k, 0)])
    corr = (counts.get("000", 0) + counts.get("111", 0)) / shots
    print(f"GHZ correlated share (000+111)={corr:.3f} -> ghz_counts.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
