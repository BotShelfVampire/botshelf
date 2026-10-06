#!/usr/bin/env python3
"""BSV recipe: swing a simple pendulum in MuJoCo and log energy drift.

Research / education / simulation only. Not a safety certification or real-hardware procedure.

Input : duration seconds (default 5), timestep hint via model (0.002).
Output: pendulum_energy.csv with time, angle, omega, kinetic, potential, total.
Original BSV code (model), MIT. Library: MuJoCo (Apache-2.0).
"""
import csv, sys
import mujoco
import numpy as np

XML = """
<mujoco model="bsv_pendulum">
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <worldbody>
    <body name="pole" pos="0 0 0">
      <joint name="hinge" type="hinge" axis="0 1 0" damping="0.05"/>
      <geom type="capsule" fromto="0 0 0 0 0 -0.3" size="0.01" mass="0.2"/>
      <site name="tip" pos="0 0 -0.3" size="0.005"/>
    </body>
  </worldbody>
</mujoco>
"""

def main(duration="5"):
    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)
    data.qpos[0] = np.deg2rad(120.0)  # start near inverted side, will fall
    data.qvel[0] = 0.0
    mujoco.mj_forward(model, data)
    tip = model.site("tip").id
    g = abs(model.opt.gravity[2])
    # tip mass approx from geom mass
    m = 0.2
    L = 0.3
    rows = []
    steps = int(float(duration) / model.opt.timestep)
    for i in range(steps):
        mujoco.mj_step(model, data)
        th = float(data.qpos[0])
        w = float(data.qvel[0])
        # potential relative to lowest point (theta=±pi... use height of tip)
        z = float(data.site_xpos[tip][2])
        pe = m * g * (z + L)  # 0 at bottom z=-L
        ke = 0.5 * m * (L * w) ** 2
        rows.append([i * model.opt.timestep, th, w, ke, pe, ke + pe])
    with open("pendulum_energy.csv", "w", newline="", encoding="utf-8") as f:
        wri = csv.writer(f)
        wri.writerow(["t_s", "theta_rad", "omega_rad_s", "ke_j", "pe_j", "total_j"])
        wri.writerows(rows)
    totals = [r[-1] for r in rows]
    drift = max(totals) - min(totals)
    print(f"wrote {len(rows)} rows -> pendulum_energy.csv; energy range drift≈{drift:.6f} J (damping present)")

if __name__ == "__main__":
    main(*sys.argv[1:])
