#!/usr/bin/env python3
"""BSV recipe: tiny 2D grid RRT from start to goal around a rectangular obstacle.

Research / education / simulation only. Toy planner — not for real robots or safety cases.

Input : optional seed (default 7), max iterations (default 800).
Output: rrt_path.csv (path waypoints) and rrt_nodes.csv (tree nodes), plus printed path length.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

# World: [0,1]x[0,1], obstacle axis-aligned box
OBS = (0.35, 0.25, 0.65, 0.75)  # xmin,ymin,xmax,ymax
START = np.array([0.1, 0.1])
GOAL = np.array([0.9, 0.9])
STEP = 0.05
GOAL_BIAS = 0.1
GOAL_TOL = 0.06

def collides(p):
    x, y = p
    return OBS[0] <= x <= OBS[2] and OBS[1] <= y <= OBS[3]

def segment_clear(a, b, n=12):
    for t in np.linspace(0, 1, n):
        if collides(a * (1 - t) + b * t):
            return False
    return True

def main(seed="7", max_iter="800"):
    rng = np.random.default_rng(int(seed))
    max_iter = int(max_iter)
    nodes = [START.copy()]
    parent = [-1]
    found = None
    for _ in range(max_iter):
        sample = GOAL.copy() if rng.random() < GOAL_BIAS else rng.random(2)
        dists = np.linalg.norm(np.stack(nodes) - sample, axis=1)
        i = int(np.argmin(dists))
        direction = sample - nodes[i]
        nrm = np.linalg.norm(direction)
        if nrm < 1e-12:
            continue
        new = nodes[i] + direction / nrm * min(STEP, nrm)
        if new[0] < 0 or new[0] > 1 or new[1] < 0 or new[1] > 1:
            continue
        if not segment_clear(nodes[i], new):
            continue
        parent.append(i)
        nodes.append(new)
        if np.linalg.norm(new - GOAL) < GOAL_TOL and segment_clear(new, GOAL):
            parent.append(len(nodes) - 1)
            nodes.append(GOAL.copy())
            found = len(nodes) - 1
            break
    with open("rrt_nodes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "x", "y", "parent"])
        for i, (p, par) in enumerate(zip(nodes, parent)):
            w.writerow([i, p[0], p[1], par])
    path = []
    if found is not None:
        i = found
        while i >= 0:
            path.append(nodes[i]); i = parent[i]
        path.reverse()
    with open("rrt_path.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["x", "y"])
        for p in path:
            w.writerow([p[0], p[1]])
    plen = float(sum(np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1))) if path else float("nan")
    print(f"RRT nodes={len(nodes)} path_pts={len(path)} length={plen:.3f} -> rrt_path.csv, rrt_nodes.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
