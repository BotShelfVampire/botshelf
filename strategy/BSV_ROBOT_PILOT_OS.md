# BSV Robot Pilot OS

Status: highest-priority frontier business thesis
Updated: 2026-10-03

## Thesis

A robot pilot is not merely a remote joystick operator.

A high-value robot pilot is a human who can:
- safely teleoperate a robot or simulation
- perform a task repeatably
- recognize failure/recovery conditions
- generate clean demonstration data
- annotate what happened
- follow task-specific SOPs
- produce evidence that a robotics team can evaluate
- improve the task recipe for the next operator

This creates a new labor layer between robotics engineering and deployed autonomy.

BSV should become infrastructure for:
1. training robot pilots
2. recording exact pilot skills
3. matching robot companies/tasks to pilots
4. packaging teleoperation procedures as reusable assets
5. collecting and reviewing training-data evidence
6. turning proven pilot workflows into autonomous-agent/robot capability products

## Why now

Modern robot-learning stacks increasingly use human demonstrations and teleoperation.

NVIDIA Isaac Teleop explicitly supports simulation and real teleoperation, standardized device interfaces, data collection, XR controllers, leader-follower devices, and robot-learning workflows. Its documentation includes simulation data collection and records demonstrations as datasets.

Therefore the scarce asset is not only robot hardware or model intelligence.

It is:
- skilled human demonstration
- repeatable operator performance
- task coverage
- quality control
- evidence
- data operations

BSV can productize that layer.

## Product concept

### Robot Pilot Academy

A simulation-first training environment.

The Academy does not begin by handing novices control of expensive hardware.

Flow:
1. choose robot/task/device
2. learn control and safety rules
3. practice in simulation
4. complete repeatable task episodes
5. record session evidence
6. review failures
7. earn a BSV Practice Record for that exact setup
8. progress to supervised real-hardware operation where a partner permits it

Do not call a BSV practice record an official government or manufacturer license.

### Pilot Passport

A machine-readable skill profile.

The passport should record exact evidence, for example:
- simulator/runtime
- robot embodiment
- controller/input device
- task
- session count
- successful/failed episodes
- date
- source revision
- reviewer
- known limitations
- whether real hardware was involved
- safety/approval scope

"Can pilot humanoids" is too broad.

"Completed 42 reviewed simulated Unitree G1 pick/place episodes using Isaac Teleop XR on revision X" is useful.

### Robot Mission Board

Companies/users can post:
- task to demonstrate
- robot/embodiment
- teleop interface
- environment
- location/remote constraints
- data needed
- episode target
- quality criteria
- compensation/budget if public
- real-hardware requirements
- NDA/privacy constraints

Initial version can be REQUEST_ONLY without escrow.

This plugs directly into BSV Request Market.

### Pilot Opportunity Feed

Pilots see:
- open simulated tasks
- data-collection missions
- operator QA/replay work
- real-hardware tasks requiring a specific passport
- skills that companies are repeatedly requesting

Builders see:
- which teleop stacks need better interfaces
- which tasks need tooling
- which pilot bottlenecks should become BSV products

### Teleop Recipe Library

Reusable operational assets:
- task SOP
- controller mapping
- retargeting settings
- environment setup
- reset procedure
- failure taxonomy
- annotation labels
- episode acceptance criteria
- recovery procedure
- data export format
- replay checklist

A teleop recipe is a sellable/reusable asset where licensing permits.

### Pilot-to-Autonomy Flywheel

1. Pilot performs task.
2. Session becomes structured evidence/data.
3. Failures reveal missing tooling.
4. Engineers improve policy/interface.
5. BSV stores the improved recipe/capability.
6. More pilots can perform the task.
7. Better datasets train better autonomy.
8. As autonomy rises, pilots move toward exception handling, QA, supervision and new-skill demonstration.

The robot pilot business does not disappear when autonomy improves.
The job moves up the stack.

## Training architecture

### Level 0 — Observer

Learn:
- robot/task vocabulary
- emergency stop concepts
- workspace boundaries
- latency and camera-view limitations
- data recording requirements
- what not to do

No control privilege implied.

### Level 1 — Simulation Pilot

Can:
- launch a supported simulation
- control a robot in a bounded task
- reset safely
- collect episodes
- label success/failure
- reproduce a task under defined conditions

### Level 2 — Data Pilot

Adds:
- dataset quality
- synchronization awareness
- task diversity
- failure/recovery capture
- annotation consistency
- session metadata
- replay review

### Level 3 — Supervised Hardware Pilot

Only after a real partner/hardware owner authorizes it.

Adds:
- hardware preflight
- local safety observer
- bounded operating area
- e-stop responsibility
- supervised recovery
- incident reporting

BSV should not grant hardware authority by itself.

### Level 4 — Mission Lead

Can:
- design pilot sessions
- define acceptance criteria
- review operators
- assign task variants
- manage data quality
- coordinate engineers/pilots
- produce a final evidence bundle

### Level 5 — Pilot Trainer / Evaluator

Can:
- train other pilots
- review exact evidence
- maintain task recipes
- identify unsafe drift
- propose new simulator curricula

This is an internal BSV/partner qualification, not a universal professional license.

## First safe curriculum

Start with simulation.

### Isaac Teleop / SO-101 simulation path

Official NVIDIA documentation currently provides:
- Isaac Lab teleoperation
- XR controller path
- SO-101 leader path
- cube stacking tasks
- demonstration recording to HDF5

BSV can add:
- setup checklist
- practice progression
- episode evidence schema
- scorecard
- replay review
- troubleshooting guide
- pilot passport entry

Do not redistribute proprietary components; link official setup and provide original BSV training/evidence layers.

### Isaac Teleop / humanoid path

NVIDIA documents end-to-end teleoperation with Isaac GR00T / Unitree G1 and simulation-first validation.

BSV can prepare a curriculum manifest without claiming that BSV has executed the hardware path.

## Pilot score

Never reduce a pilot to a single opaque number.

Show component metrics:
- task completion
- repeatability
- intervention count
- collision/safety violations in simulation
- recovery quality
- annotation completeness
- dataset integrity
- latency handling
- reviewer status

Any composite score must expose its formula.

Do not compare pilots across fundamentally different robots/tasks without normalization.

## Business models

### 1. Training assets

Free or paid simulator courses / recipes / task packs.

Existing BSV marketplace economics can support creator-supplied training assets where appropriate.

### 2. Practice verification

BSV can charge for structured evidence review later.

Do not sell "certification" as a legal license.

Possible product:
"BSV Reviewed Practice Record"

### 3. Mission marketplace

Robot companies post missions.
Qualified pilots apply.

Initially:
- request/matching only
- no escrow
- compensation handled outside BSV unless a dedicated service-payment system is later implemented

Later:
- service contracts
- escrow/milestones
- BSV take rate
- dispute workflow

Do not bolt services escrow onto current product checkout without a dedicated design.

### 4. Data factory

BSV can coordinate:
- pilot recruitment
- session recipe
- operator training
- episode collection
- QA/replay
- dataset packaging

This becomes a B2B service.

The valuable deliverable is not "hours worked".
It is accepted, traceable task episodes.

### 5. Enterprise Pilot OS

Private tenant for robotics firms:
- internal mission board
- internal pilot roster
- private task recipes
- dataset/evidence tracking
- reviewer workflows
- version control
- training progression

### 6. Pilot tooling marketplace

Engineers sell:
- teleop interfaces
- dashboards
- retargeting configs
- annotation tools
- QA/replay tooling
- simulation scenes
- data converters

This is where the AI engineer monetization thesis meets robotics.

## Growth loop

Robot company has missing data/task
→ posts mission/request
→ BSV exposes demand
→ engineer creates tooling
→ pilots train
→ pilots collect evidence/data
→ company accepts episodes
→ tooling and recipes improve
→ BSV accumulates capability graph
→ new companies arrive because supply and pilot skill already exist

## Trust and safety

Operator identity can remain pseudonymous publicly where appropriate.

But pilot mission evidence must be attributable internally to a stable account.

For real hardware:
- partner owns authorization
- explicit equipment/runtime version
- local safety requirements
- human supervisor where required
- emergency stop procedure
- no autonomous escalation from simulation permission to hardware permission

Sensitive video/sensor data must not be made public by default.

Medical, defense, weapons, hazardous industrial tasks and other regulated/high-risk use cases require separate policy gates and may be excluded.

## BSV machine interfaces

Robot Pilot assets should use:
- Universal Capability Manifest
- Demand Request schema
- Robot Pilot Profile schema
- Teleop Session Evidence schema

This allows future AI agents to ask:
"Find pilots with exact task evidence for this robot/runtime"
instead of scraping profile prose.

## First implementation tranche

1. add Robot Pilot sector to frontier catalog
2. create pilot profile schema
3. create teleop session evidence schema
4. create simulation curriculum schema
5. add original Isaac Teleop simulation curriculum starter
6. add mission/request type compatible with Request Market
7. create Robot Pilot Academy landing concept inside the upcoming frontier layer
8. do NOT expose unsupported real-hardware credentials
9. measure interest before building a full staffing marketplace

## Success metrics

Training:
- training starts
- completed simulator modules
- reviewed practice records
- repeat practice
- failure/recovery capture quality

Marketplace:
- robot missions posted
- qualified pilot applications
- mission fill rate
- accepted episodes
- repeat company demand

Supply:
- pilot tools published
- recipes published
- engineer-to-robotics seller activation

Revenue:
- training asset GMV
- pilot tooling GMV
- review revenue
- mission/service revenue later
- enterprise Pilot OS revenue later
