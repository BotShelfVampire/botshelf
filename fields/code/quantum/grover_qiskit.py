#!/usr/bin/env python3
"""BSV recipe: Grover search for one marked bitstring, measured vs. theory (Qiskit reference primitives).

Input : marked bitstring (default 101), shots (default 2000). Iterations = round(pi/4 * sqrt(N) - 1/2).
Output: grover_counts.csv and a printed success rate next to the textbook value sin^2((2k+1)*theta), sin(theta)=1/sqrt(N).
Original BSV code, MIT. Library: Qiskit (Apache-2.0). Simulator only (StatevectorSampler).
"""
import csv, math, sys
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate
from qiskit.primitives import StatevectorSampler

def oracle(qc, marked):
    n = len(marked)
    for i, bit in enumerate(reversed(marked)):     # qubit 0 = rightmost bit
        if bit == "0":
            qc.x(i)
    qc.h(n - 1); qc.append(MCXGate(n - 1), list(range(n))); qc.h(n - 1)
    for i, bit in enumerate(reversed(marked)):
        if bit == "0":
            qc.x(i)

def diffuser(qc, n):
    qc.h(range(n)); qc.x(range(n))
    qc.h(n - 1); qc.append(MCXGate(n - 1), list(range(n))); qc.h(n - 1)
    qc.x(range(n)); qc.h(range(n))

def main(marked="101", shots="2000"):
    n = len(marked); N = 2 ** n
    k = max(1, round(math.pi / 4 * math.sqrt(N) - 0.5))
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for _ in range(k):
        oracle(qc, marked); diffuser(qc, n)
    qc.measure_all()
    counts = StatevectorSampler(seed=11).run([qc], shots=int(shots)).result()[0].data.meas.get_counts()
    with open("grover_counts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["bitstring", "count"])
        for b, c in sorted(counts.items(), key=lambda kv: -kv[1]):
            w.writerow([b, c])
    theta = math.asin(1 / math.sqrt(N))
    print(f"N={N}, iterations={k}, marked={marked}")
    print(f"measured success {counts.get(marked, 0) / int(shots):.3f}  theory {math.sin((2 * k + 1) * theta) ** 2:.3f}  random guess {1 / N:.3f}")

if __name__ == "__main__":
    main(*sys.argv[1:])
