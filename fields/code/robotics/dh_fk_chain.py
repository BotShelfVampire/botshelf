#!/usr/bin/env python3
"""BSV recipe: forward kinematics for a short DH (modified) chain → pose table.

Research / education / simulation only.

Input : comma-separated joint angles in radians (default 0.2,0.4,-0.3) for a fixed 3-revolute demo chain.
Output: dh_fk.csv with link index, x,y,z (meters) of each frame origin, and final RPY (xyz, rad).
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

# Modified DH: alpha_{i-1}, a_{i-1}, d_i, theta_i  (Craig style)
# Demo 3R anthropomorphic-ish lengths (meters)
DH = [
    # alpha, a, d, theta_offset
    (0.0, 0.0, 0.10, 0.0),
    (-np.pi / 2, 0.0, 0.0, 0.0),
    (0.0, 0.25, 0.0, 0.0),
]

def T_mdh(alpha, a, d, theta):
    ca, sa = np.cos(alpha), np.sin(alpha)
    ct, st = np.cos(theta), np.sin(theta)
    return np.array([
        [ct, -st, 0, a],
        [st * ca, ct * ca, -sa, -sa * d],
        [st * sa, ct * sa, ca, ca * d],
        [0, 0, 0, 1],
    ], dtype=float)

def rpy_xyz(R):
    # XYZ fixed angles
    sy = -R[2, 0]
    cy = np.sqrt(max(0.0, 1 - sy * sy))
    if cy > 1e-8:
        rx = np.arctan2(R[2, 1], R[2, 2])
        rz = np.arctan2(R[1, 0], R[0, 0])
    else:
        rx = np.arctan2(-R[1, 2], R[1, 1])
        rz = 0.0
    ry = np.arctan2(sy, cy)
    return float(rx), float(ry), float(rz)

def main(angles="0.2,0.4,-0.3"):
    q = [float(x) for x in angles.split(",")]
    if len(q) != len(DH):
        raise SystemExit(f"need {len(DH)} angles, got {len(q)}")
    T = np.eye(4)
    rows = [[0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    for i, ((alpha, a, d, off), qi) in enumerate(zip(DH, q), start=1):
        T = T @ T_mdh(alpha, a, d, qi + off)
        rpy = rpy_xyz(T[:3, :3])
        rows.append([i, T[0, 3], T[1, 3], T[2, 3], *rpy])
    with open("dh_fk.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame", "x_m", "y_m", "z_m", "roll_rad", "pitch_rad", "yaw_rad"])
        w.writerows(rows)
    tip = rows[-1]
    print(f"frames {len(rows)} -> dh_fk.csv; tip xyz=({tip[1]:.4f},{tip[2]:.4f},{tip[3]:.4f})")

if __name__ == "__main__":
    main(*sys.argv[1:])
