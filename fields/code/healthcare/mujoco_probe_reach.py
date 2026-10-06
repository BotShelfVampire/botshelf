#!/usr/bin/env python3
"""BSV recipe: probe-tip positioning test for a 2-link arm in MuJoCo, with logged accuracy metrics.

Research / education / simulation only. Not a medical device, not clinical guidance.

Input : target points in mm (default four points in the arm's workspace), controller gain kp (default 60),
        tolerance in mm (default 1.0).
Output: probe_reach.csv with, per target: time to first enter the tolerance, time it stays inside, final error, peak overshoot past
        the target and whether the target was reached within 3 s of simulated time.
Original BSV code (model and controller), MIT. Library: MuJoCo (Apache-2.0).
"""
import csv, sys
import mujoco
import numpy as np

XML = """
<mujoco model="bsv_probe_arm">
  <option timestep="0.002" gravity="0 0 0"/>
  <worldbody>
    <body name="link1" pos="0 0 0">
      <joint name="j1" type="hinge" axis="0 0 1" damping="2.0"/>
      <geom type="capsule" fromto="0 0 0 0.12 0 0" size="0.008" mass="0.15"/>
      <body name="link2" pos="0.12 0 0">
        <joint name="j2" type="hinge" axis="0 0 1" damping="1.2"/>
        <geom type="capsule" fromto="0 0 0 0.10 0 0" size="0.006" mass="0.08"/>
        <site name="tip" pos="0.10 0 0" size="0.003"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <position name="a1" joint="j1" kp="KP"/>
    <position name="a2" joint="j2" kp="KP"/>
  </actuator>
</mujoco>
"""
L1, L2 = 0.12, 0.10

def ik(x, y):
    """Closed-form inverse kinematics of a planar 2-link arm (elbow-down)."""
    c2 = (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(c2) > 1:
        raise ValueError(f"target ({x:.3f}, {y:.3f}) is outside the workspace")
    q2 = np.arccos(c2)
    q1 = np.arctan2(y, x) - np.arctan2(L2 * np.sin(q2), L1 + L2 * np.cos(q2))
    return q1, q2

def main(targets="150,60;120,-80;180,0;90,120", kp="60", tol_mm="1.0"):
    model = mujoco.MjModel.from_xml_string(XML.replace("KP", str(float(kp))))
    data = mujoco.MjData(model)
    tip = model.site("tip").id
    rows = []
    for t in targets.split(";"):
        tx, ty = (float(v) / 1000 for v in t.split(","))
        q1, q2 = ik(tx, ty)
        start = data.site_xpos[tip][:2].copy()
        data.ctrl[:] = [q1, q2]
        t_in, t_settle, peak_over = None, None, 0.0
        direction = np.array([tx, ty]) - start
        direction = direction / (np.linalg.norm(direction) or 1)
        for step in range(int(3.0 / model.opt.timestep)):
            mujoco.mj_step(model, data)
            p = data.site_xpos[tip][:2]
            err = np.linalg.norm(p - [tx, ty]) * 1000
            peak_over = max(peak_over, float(np.dot(p - [tx, ty], direction)) * 1000)
            now = (step + 1) * model.opt.timestep
            if t_in is None and err <= float(tol_mm):
                t_in = now
            if err > float(tol_mm):
                t_settle = None
            elif t_settle is None:
                t_settle = now
        rows.append({"target_mm": t, "time_to_tol_s": round(t_in, 3) if t_in else "",
                     "settled_at_s": round(t_settle, 3) if t_settle else "", "final_err_mm": round(float(err), 3),
                     "overshoot_mm": round(peak_over, 3), "reached": t_in is not None})
    with open("probe_reach.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r)

if __name__ == "__main__":
    main(*sys.argv[1:])
