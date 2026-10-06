#!/usr/bin/env python3
"""BSV recipe: relative SE(3) pose T_A^{-1} T_B from two XYZ+RPY poses.

Research / education / simulation only. Degrees for RPY input; meters for translation.

Input : pose A as x,y,z,roll,pitch,yaw then pose B (defaults: A origin, B small offset).
Output: se3_relative.csv with relative xyz and rpy_xyz (rad), plus 4x4 printed summary.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, sys
import numpy as np

def rpy_to_R(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx

def R_to_rpy(R):
    pitch = np.arcsin(np.clip(-R[2, 0], -1, 1))
    if abs(np.cos(pitch)) < 1e-8:
        roll = 0.0
        yaw = np.arctan2(-R[0, 1], R[1, 1])
    else:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    return float(roll), float(pitch), float(yaw)

def pose_to_T(x, y, z, roll, pitch, yaw):
    T = np.eye(4)
    T[:3, :3] = rpy_to_R(roll, pitch, yaw)
    T[:3, 3] = [x, y, z]
    return T

def main(ax="0", ay="0", az="0", ar="0", ap="0", aw="0",
         bx="0.1", by="0.05", bz="0.02", br="0.2", bp="0.1", bw="-0.3"):
    nums = [float(v) for v in (ax, ay, az, ar, ap, aw, bx, by, bz, br, bp, bw)]
    Ta = pose_to_T(*nums[:6])
    Tb = pose_to_T(*nums[6:])
    Trel = np.linalg.inv(Ta) @ Tb
    x, y, z = Trel[:3, 3]
    roll, pitch, yaw = R_to_rpy(Trel[:3, :3])
    with open("se3_relative.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x_m", "y_m", "z_m", "roll_rad", "pitch_rad", "yaw_rad"])
        w.writerow([x, y, z, roll, pitch, yaw])
    print(f"T_A^{-1} T_B xyz=({x:.4f},{y:.4f},{z:.4f}) rpy=({roll:.4f},{pitch:.4f},{yaw:.4f}) -> se3_relative.csv")

if __name__ == "__main__":
    main(*sys.argv[1:13])
