#!/usr/bin/env python3
"""BSV recipe: Swap test — estimate |⟨ψ|φ⟩|² from an ancilla (Qiskit Aer).

Research / education only. Simulator only.
Input : theta_psi, theta_phi in radians for RX|0⟩ states (defaults 0.0 0.8), shots (default 4000).
Output: swap_test.csv with p0, overlap_est, analytic_overlap_sq, abs_err.
Original BSV code, MIT. Libraries: Qiskit, Qiskit Aer (Apache-2.0).
"""
import csv, math, sys
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def main(theta_psi="0.0", theta_phi="0.8", shots="4000"):
    th_a, th_b = float(theta_psi), float(theta_phi)
    shots = int(shots)
    # wires: 0=ancilla, 1=psi, 2=phi
    qc = QuantumCircuit(3, 1)
    qc.rx(th_a, 1)
    qc.rx(th_b, 2)
    qc.h(0)
    qc.cswap(0, 1, 2)
    qc.h(0)
    qc.measure(0, 0)
    sim = AerSimulator(seed_simulator=13)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    p0 = counts.get("0", 0) / shots
    # For pure states, P(0) = (1 + |⟨ψ|φ⟩|²) / 2  =>  |⟨|² = 2P0 - 1
    overlap_est = max(0.0, min(1.0, 2 * p0 - 1))
    # |0⟩ and RX(θ)|0⟩: ⟨0|RX(θ)|0⟩ = cos(θ/2); two RX states: cos((θa-θb)/2) up to global phase
    # ⟨ψ|φ⟩ for RX(a)|0⟩ and RX(b)|0⟩ = cos((a-b)/2) * (phase); magnitude cos((a-b)/2)
    ana = math.cos((th_a - th_b) / 2.0) ** 2
    err = abs(overlap_est - ana)
    with open("swap_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["theta_psi", "theta_phi", "p0", "overlap_est", "analytic_overlap_sq", "abs_err", "shots"])
        w.writeheader()
        w.writerow({"theta_psi": th_a, "theta_phi": th_b, "p0": p0, "overlap_est": overlap_est,
                    "analytic_overlap_sq": ana, "abs_err": err, "shots": shots})
    print(f"P(0)={p0:.3f} |overlap|²≈{overlap_est:.3f} analytic={ana:.3f} |err|={err:.3f} -> swap_test.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
