#!/usr/bin/env python3
"""BSV recipe: a Bell pair on an ideal simulator vs. a simple noisy simulator (Qiskit + Qiskit Aer).

Input : one-qubit and two-qubit depolarising error rates (defaults 0.01 and 0.03 — example settings,
        not the figures of any real device), shots (default 4000).
Output: bell_counts.csv with counts per outcome for both runs, and the share of correlated outcomes (00 + 11).
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

def main(p1="0.01", p2="0.03", shots="4000"):
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.cx(0, 1); qc.measure([0, 1], [0, 1])
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(float(p1), 1), ["h", "sx", "x", "rz"])
    noise.add_all_qubit_quantum_error(depolarizing_error(float(p2), 2), ["cx"])
    noise.add_all_qubit_readout_error(ReadoutError([[0.98, 0.02], [0.02, 0.98]]))
    results = {}
    for label, sim in (("ideal", AerSimulator(seed_simulator=7)), ("noisy", AerSimulator(noise_model=noise, seed_simulator=7))):
        tc = transpile(qc, sim)
        results[label] = sim.run(tc, shots=int(shots)).result().get_counts()
    with open("bell_counts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["outcome", "ideal", "noisy"])
        for k in ("00", "01", "10", "11"):
            w.writerow([k, results["ideal"].get(k, 0), results["noisy"].get(k, 0)])
    for label, c in results.items():
        corr = (c.get("00", 0) + c.get("11", 0)) / int(shots)
        print(f"{label:5s} {dict(sorted(c.items()))}  correlated share {corr:.3f}")

if __name__ == "__main__":
    main(*sys.argv[1:])
