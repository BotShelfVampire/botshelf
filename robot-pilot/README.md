# BSV Robot Pilot

BSV Robot Pilot is a simulation-first training, evidence, mission and tooling layer for teleoperation work.

The premise is simple:

**human skill → teleoperation session → structured evidence/data → better tooling → better robot autonomy**

BSV should not treat a robot pilot as "someone who can move a robot."

A useful pilot record must identify the exact:
- task
- robot/embodiment
- runtime/version
- input device
- environment
- session/episode evidence
- review status
- limitations

## Current source

- [Business/product strategy](../strategy/BSV_ROBOT_PILOT_OS.md)
- [Pilot profile schema](../schemas/bsv-robot-pilot-profile.schema.json)
- [Teleop session evidence schema](../schemas/bsv-teleop-session-evidence.schema.json)
- [Curriculum schema](../schemas/bsv-robot-pilot-curriculum.schema.json)
- [Isaac Teleop SO-101 simulation starter](curricula/isaac-teleop-so101-sim-v1.json)

## First target

Simulation first.

The initial curriculum is based on NVIDIA's current Isaac Teleop / Isaac Lab simulation path, including SO-101 demonstration collection. BSV adds an original practice/evidence/review layer rather than redistributing NVIDIA code or pretending BSV has executed a real hardware session.

Official references:
- https://nvidia.github.io/IsaacTeleop/main/getting_started/quick_start.html
- https://nvidia.github.io/IsaacTeleop/main/getting_started/lerobot/data_collection_sim.html
- https://github.com/NVIDIA/IsaacCapture

## Important boundary

A BSV Practice Record is not:
- a government license
- a manufacturer certification
- permission to operate real hardware
- proof of general ability across all robots

Real-hardware control requires the robot/hardware owner to authorize it and define local safety requirements.

## Business paths

- training assets
- teleop recipe/tool marketplace
- mission matching
- pilot opportunity feed
- reviewed practice records
- data collection / episode QA service
- later enterprise Pilot OS

Do not add escrow to the current BSV product checkout without a dedicated service-payment design.
