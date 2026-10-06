#!/usr/bin/env python3
"""BSV recipe: Bernstein–Vazirani — recover a secret bitstring with one oracle query (Qiskit Aer).

Research / education only. Simulator only — not a hardware-advantage claim.
Input : secret bitstring of length 3–6 using 0/1 (default 101), shots (default 2000).
Output: bv_result.csv with counts, secret, recovered, match.
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def main(secret="101", shots="2000"):
    secret = "".join(ch for ch in (secret or "101") if ch in "01")
    if not (3 <= len(secret) <= 6):
        raise SystemExit("secret must be 3–6 bits of 0/1")
    shots = int(shots)
    n = len(secret)
    qc = QuantumCircuit(n + 1, n)
    qc.x(n); qc.h(n)
    qc.h(range(n))
    for i, bit in enumerate(reversed(secret)):  # qiskit measure bit order: c0 = qubit 0
        if bit == "1":
            qc.cx(i, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    sim = AerSimulator(seed_simulator=11)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    # Aer returns bitstrings with qubit n-1 on the left
    recovered = max(counts, key=counts.get)
    # Map measured string (q_n-1 … q_0) to secret written left-to-right as s_{n-1}…s_0
    match = recovered == secret
    with open("bv_result.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["outcome", "count"])
        for k in sorted(counts):
            w.writerow([k, counts[k]])
        w.writerow(["secret", secret])
        w.writerow(["recovered", recovered])
        w.writerow(["match", int(match)])
        w.writerow(["top_share", f"{counts[recovered] / shots:.4f}"])
    print(f"secret={secret} recovered={recovered} match={int(match)} top_share={counts[recovered]/shots:.3f} -> bv_result.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
