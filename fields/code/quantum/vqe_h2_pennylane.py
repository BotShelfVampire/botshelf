#!/usr/bin/env python3
"""BSV recipe: your first VQE on a simulator — H2 ground-state energy with PennyLane.

Input : H-H bond length in angstrom (default 0.74), optimiser steps (default 60).
Output: vqe_h2.csv (step, energy in Hartree) and a printed comparison with exact diagonalisation
        of the same qubit Hamiltonian (STO-3G basis, 4 qubits). Simulator only (default.qubit).
Original BSV code, MIT. Library: PennyLane (Apache-2.0); Hamiltonian from PennyLane's built-in qchem (differentiable Hartree-Fock).
"""
import csv, sys
import pennylane as qml
from pennylane import numpy as np

def main(bond_angstrom="0.74", steps="60"):
    d = float(bond_angstrom) / 0.529177210903          # angstrom -> bohr (CODATA 2018 Bohr radius)
    symbols, coords = ["H", "H"], np.array([0.0, 0.0, -d / 2, 0.0, 0.0, d / 2])
    H, n_qubits = qml.qchem.molecular_hamiltonian(symbols, coords)
    hf = qml.qchem.hf_state(electrons=2, orbitals=n_qubits)
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev)
    def energy(theta):
        qml.BasisState(hf, wires=range(n_qubits))
        qml.DoubleExcitation(theta[0], wires=[0, 1, 2, 3])
        return qml.expval(H)

    opt = qml.GradientDescentOptimizer(stepsize=0.4)
    theta = np.array([0.0], requires_grad=True)
    trace = []
    for i in range(int(steps)):
        theta, e = opt.step_and_cost(energy, theta)
        trace.append((i, float(e)))
    final = float(energy(theta))
    exact = float(min(np.linalg.eigvalsh(qml.matrix(H, wire_order=range(n_qubits)))))
    with open("vqe_h2.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["step", "energy_hartree"]); w.writerows(trace)
    print(f"qubits {n_qubits}, terms {len(H.terms()[0])}")
    print(f"HF start   {trace[0][1]:.6f} Ha")
    print(f"VQE final  {final:.6f} Ha  (theta = {float(theta[0]):.4f})")
    print(f"exact      {exact:.6f} Ha  (same Hamiltonian, numpy eigvalsh)")
    print(f"error      {abs(final - exact) * 1000:.3f} mHa  (chemical accuracy is about 1.6 mHa)")

if __name__ == "__main__":
    main(*sys.argv[1:])
