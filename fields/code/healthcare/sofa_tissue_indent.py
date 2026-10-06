#!/usr/bin/env python3
"""BSV recipe (NOT RUN BY BSV): soft-tissue block indentation in SOFA, logging force vs. displacement.

Research / education / simulation only. A warm-up for needle-insertion studies: it models only linear-elastic
indentation of a block, not puncture, friction or needle bending.

Run   : runSofa -l SofaPython3 sofa_tissue_indent.py   (SOFA v24.06 or later with the SofaPython3 plugin)
Output: indent_log.csv  (step, applied force in N, downward displacement of the top-centre node in mm)
Component names follow SOFA v24.06; check them against the SOFA version you install.
Original BSV code, MIT. SOFA and SofaPython3 are LGPL-2.1.
"""
import csv
import Sofa
import Sofa.Core

NX, NY, NZ = 7, 7, 4                      # grid nodes; odd NX/NY gives an exact top-centre node
SIZE = (0.04, 0.04, 0.02)                 # block size in metres (4 x 4 x 2 cm)
YOUNG = 5000.0                            # Pa - example value for a soft gel phantom; change and compare
POISSON = 0.45
TOP_CENTRE = (NX // 2) + NX * ((NY // 2) + NY * (NZ - 1))
MAX_FORCE = 0.5                           # N, reached after RAMP_STEPS
RAMP_STEPS = 400


class IndentLogger(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mo, self.ff = kwargs["mo"], kwargs["ff"]
        self.step, self.z0, self.rows = 0, None, []

    def onAnimateBeginEvent(self, event):
        self.step += 1
        f = MAX_FORCE * min(self.step / RAMP_STEPS, 1.0)
        self.ff.forces.value = [[0.0, 0.0, -f]]
        z = self.mo.position.value[TOP_CENTRE][2]
        self.z0 = z if self.z0 is None else self.z0
        self.rows.append((self.step, round(f, 5), round((self.z0 - z) * 1000, 4)))
        if self.step % 50 == 0:
            with open("indent_log.csv", "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["step", "force_N", "displacement_mm"]); w.writerows(self.rows)


def createScene(root):
    root.gravity = [0, 0, 0]
    root.dt = 0.005
    root.addObject("RequiredPlugin", pluginName=[
        "Sofa.Component.ODESolver.Backward", "Sofa.Component.LinearSolver.Iterative",
        "Sofa.Component.StateContainer", "Sofa.Component.Topology.Container.Grid",
        "Sofa.Component.SolidMechanics.FEM.Elastic", "Sofa.Component.Mass",
        "Sofa.Component.Engine.Select", "Sofa.Component.Constraint.Projective",
        "Sofa.Component.MechanicalLoad", "Sofa.Component.Visual"])
    root.addObject("DefaultAnimationLoop")
    root.addObject("VisualStyle", displayFlags="showBehaviorModels showForceFields")
    tissue = root.addChild("Tissue")
    tissue.addObject("EulerImplicitSolver", rayleighStiffness=0.1, rayleighMass=0.1)
    tissue.addObject("CGLinearSolver", iterations=50, tolerance=1e-9, threshold=1e-9)
    tissue.addObject("RegularGridTopology", name="grid", n=[NX, NY, NZ], min=[0, 0, 0], max=list(SIZE))
    mo = tissue.addObject("MechanicalObject", name="dofs")
    tissue.addObject("UniformMass", totalMass=0.035)
    tissue.addObject("HexahedronFEMForceField", youngModulus=YOUNG, poissonRatio=POISSON, method="large")
    tissue.addObject("BoxROI", name="base", box=[-0.001, -0.001, -0.001, SIZE[0] + 0.001, SIZE[1] + 0.001, 0.001])
    tissue.addObject("FixedProjectiveConstraint", indices="@base.indices")
    ff = tissue.addObject("ConstantForceField", name="probe", indices=[TOP_CENTRE], forces=[[0, 0, 0]])
    tissue.addObject(IndentLogger(name="logger", mo=mo, ff=ff))
    return root
