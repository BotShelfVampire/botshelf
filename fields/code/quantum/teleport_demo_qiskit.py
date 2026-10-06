#!/usr/bin/env python3
"""BSV recipe: quantum teleportation protocol demo on a simulator (Qiskit Aer).

Research / education only. Shows Alice→Bob state transfer via entanglement + classical bits.
Not a communications product and not a hardware claim.

Input : Alice's initial RX angle radians (default 0.7), shots (default 4000).
Output: teleport_counts.csv of Bob's measured bit vs ideal Z-basis probabilities for the prepared state.
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, math, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def main(theta="0.7", shots="4000"):
    theta = float(theta); shots = int(shots)
    # q0 = message (Alice), q1 = Alice's Bell half, q2 = Bob
    qc = QuantumCircuit(3, 1)
    qc.rx(theta, 0)                 # message state
    qc.h(1); qc.cx(1, 2)            # Bell pair
    qc.cx(0, 1); qc.h(0)            # Bell measurement on Alice
    qc.cx(1, 2); qc.cz(0, 2)        # Bob corrections (deferred to gates for demo)
    qc.measure(2, 0)
    sim = AerSimulator(seed_simulator=7)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    # Ideal |ψ> = RX(θ)|0> => P(0)=cos²(θ/2), P(1)=sin²(θ/2)
    p0 = math.cos(theta / 2) ** 2
    p1 = math.sin(theta / 2) ** 2
    c0 = counts.get("0", 0); c1 = counts.get("1", 0)
    with open("teleport_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bit", "count", "empirical_share", "ideal_share"])
        w.writerow(["0", c0, f"{c0/shots:.4f}", f"{p0:.4f}"])
        w.writerow(["1", c1, f"{c1/shots:.4f}", f"{p1:.4f}"])
        w.writerow(["theta_rad", theta, "", ""])
    print(f"teleport θ={theta:.3f} Bob P0={c0/shots:.3f} (ideal {p0:.3f}) -> teleport_counts.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
