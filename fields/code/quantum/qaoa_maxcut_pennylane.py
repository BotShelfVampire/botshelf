#!/usr/bin/env python3
"""BSV recipe: QAOA for Max-Cut on a small graph, checked against brute force (PennyLane simulator).

Input : edge list (default: 5-node graph "0-1,1-2,2-3,3-4,4-0,0-2"), QAOA depth p (default 2), steps (default 80).
Output: qaoa_result.json with the most likely bitstring, its cut size, the brute-force optimum and the
        probability QAOA puts on optimal cuts.
Original BSV code, MIT. Library: PennyLane (Apache-2.0).
"""
import itertools, json, sys
import networkx as nx
import pennylane as qml
from pennylane import numpy as np

def cut(bits, edges):
    return sum(1 for a, b in edges if bits[a] != bits[b])

def main(edge_str="0-1,1-2,2-3,3-4,4-0,0-2", p="2", steps="80"):
    edges = [tuple(int(x) for x in e.split("-")) for e in edge_str.split(",")]
    g = nx.Graph(edges); n = g.number_of_nodes(); p = int(p)
    cost_h, mixer_h = qml.qaoa.maxcut(g)
    dev = qml.device("default.qubit", wires=n)

    def layers(params):
        for w in range(n):
            qml.Hadamard(wires=w)
        for gamma, alpha in params:
            qml.qaoa.cost_layer(gamma, cost_h)
            qml.qaoa.mixer_layer(alpha, mixer_h)

    @qml.qnode(dev)
    def cost(params):
        layers(params); return qml.expval(cost_h)

    @qml.qnode(dev)
    def probs(params):
        layers(params); return qml.probs(wires=range(n))

    np.random.seed(3)
    params = np.array(np.random.uniform(0, np.pi / 2, (p, 2)), requires_grad=True)
    opt = qml.AdamOptimizer(0.05)
    for _ in range(int(steps)):
        params = opt.step(cost, params)
    pr = probs(params)
    best_cut = max(cut(b, edges) for b in itertools.product([0, 1], repeat=n))
    top = int(np.argmax(pr)); top_bits = [int(x) for x in format(top, f"0{n}b")]
    p_opt = float(sum(pr[i] for i in range(2 ** n) if cut([int(x) for x in format(i, f"0{n}b")], edges) == best_cut))
    res = {"edges": edges, "p": p, "most_likely": "".join(map(str, top_bits)), "its_cut": cut(top_bits, edges),
           "brute_force_max_cut": best_cut, "prob_on_optimal_cuts": round(p_opt, 4),
           "random_guess_prob": round(sum(1 for b in itertools.product([0, 1], repeat=n) if cut(b, edges) == best_cut) / 2 ** n, 4)}
    json.dump(res, open("qaoa_result.json", "w"), indent=1)
    print(json.dumps(res))

if __name__ == "__main__":
    main(*sys.argv[1:])
