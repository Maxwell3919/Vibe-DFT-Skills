# LASP public capability and workflow guide

Use this guide to turn public LASP 3.7 literature into a scientifically bounded
plan. It intentionally contains no LASP input keywords, filenames, units,
defaults, completion markers, or restart semantics. Those require the
authorized 3.7.3 manual/examples and remain blocking.

## Contents

- [Evidence ceiling](#evidence-ceiling)
- [Public architecture](#public-architecture)
- [Select a workflow family](#select-a-workflow-family)
- [Close the PES evaluator and model](#close-the-pes-evaluator-and-model)
- [Plan SSW structure exploration](#plan-ssw-structure-exploration)
- [Plan reaction exploration](#plan-reaction-exploration)
- [Plan active learning and NN construction](#plan-active-learning-and-nn-construction)
- [Plan MD without inventing syntax](#plan-md-without-inventing-syntax)
- [Attest opaque artifacts](#attest-opaque-artifacts)
- [Interpret performance and licensing](#interpret-performance-and-licensing)
- [Accept, weaken, or stop](#accept-weaken-or-stop)

## Evidence ceiling

Distinguish four layers:

1. **Author literature fact** — a method/capability is described for LASP 3.7
   or an earlier method family.
2. **Official public-page fact** — the current LASP Hub page identifies the
   3.7.3 editions, broad environment, executable entry, and access route.
3. **Operational heuristic** — a useful planning practice that is not a LASP
   default and must be project-validated.
4. **Authorized operational fact** — exact syntax/units/files/markers from the
   retained matching distribution. None is available in this repository.

Only the first two layers are currently populated. A paper, a public download
button, or a discovered binary cannot establish layer 4. The deterministic
guard inventories opaque artifacts and must continue to return incomplete for
input, output, trajectory provenance, and operational readiness.

The current guard vocabulary covers only NVE/NVT/NPT, global-structure-search,
and reaction-search as documentary task labels. PES-only evaluation, active
learning/NN construction, ASOP, and ML-interface remain reference-guided plans
without a machine-readable task profile; do not disguise them as another task.
Even the two search labels still use an MD-shaped request containing timestep,
equilibration/production, and mean/block-mean observable fields. Do not invent
values for irrelevant fields to force `plan=pass`; a pass cannot establish the
search-space, duplicate, coverage, recurrence, or termination contract below.

## Public architecture

The LASP authors' 2024 review describes LASP 3.7 as three connected parts:

- potential-energy and gradient evaluation;
- global potential-energy-surface (PES) sampling;
- neural-network training.

The paper describes G-NN potentials, the many-body-corrected G-MBNN model,
interfaces to Gaussian, VASP, CP2K, LAMMPS, and Quantum ESPRESSO, SSW-based
structure and pathway sampling, transition-state methods, conventional MD, and
an active-learning loop combining DFT, SSW sampling, and NN training.

This is an architectural map, not evidence that every 3.7.3 edition contains
every interface or that a particular user is licensed to use it. Resolve the
edition, package contents, external-engine license, and exact manual before an
operational claim.

## Select a workflow family

| Scientific intent | Publicly described LASP concept | Evidence that remains mandatory |
|---|---|---|
| evaluate a known structure | G-NN/G-MBNN or an external PES interface | exact model/interface/package, input/output grammar, units, model domain |
| explore minima/structures | SSW global PES sampling; fixed- or variable-cell context | search bounds, operational controls, duplicate rule, termination, independent coverage |
| surface phase search | ASOP coupled to SSW-NN under grand-canonical conditions | script/package access, chemical-potential/cell protocol, exact version interface |
| interface search | ML-interface plus SSW global optimization | lattice/orientation generation rules, composition moves, exact script/package contract |
| reaction/pathway search | SSW-RS, CBD/DESW, ML-TS, or MMLPS depending on the question | algorithm-specific operational contract, TS/path validation, network completeness rule |
| build a potential | DFT + SSW sampling + NN training active-learning loop | training grammar, labels/units, split/domain policy, model files, stopping rule |
| run dynamics | literature-level NVE/NVT/NPT and restraint capability | exact ensemble/integrator/timestep/seed/output/restart syntax and validation |

Do not route every problem to “SSW.” Structure discovery, transition-state
location, reaction-network exploration, active learning, and MD have different
estimators and stopping conditions.

## Close the PES evaluator and model

Every search or trajectory depends on one explicit PES provider. Record:

- LASP edition/version and the exact evaluation route;
- external engine or NN/G-MBNN model identity and SHA-256;
- model training-data/reference-method lineage and independent license;
- supported elements, compositions, charge/spin states, phases, pressure and
  temperature range, defects/interfaces/reaction environments, and short-range
  treatment;
- energy, force, stress/virial, and application-observable validation;
- extrapolation/domain-risk policy and the action taken on violation.

The author review emphasizes that an MLP is reliable mainly for interpolation
relative to its training domain and that target-relevant data quality controls
transferability. Do not treat the label “global” in G-NN as unlimited chemical
or configurational transferability.

G-MBNN adds explicit many-body correction functions to improve description of
complex PES regions, including metastable/transition structures. That method
claim does not validate a particular trained model. Require held-out and
application-specific comparisons against the chosen reference method.

## Plan SSW structure exploration

The author review describes one SSW Monte Carlo step conceptually as:

1. climb from a minimum toward a high-energy configuration using a softened
   random direction and bias-potential-driven movement;
2. relax to a minimum;
3. accept or reject through Metropolis Monte Carlo.

Consecutive minima form an SSW trajectory. Literature describes applications
to clusters, crystals, surfaces, interfaces, and fixed/variable cells. Do not
invent an input control from these concepts.

Before an authorized operational translation, define at the scientific level:

- composition/stoichiometry and whether it is fixed or grand canonical;
- periodicity, cell variation, surface/interface orientation, vacuum and
  substrate constraints;
- PES provider/model version and domain limits;
- independent initial structures and random-seed policy;
- allowed structural/compositional moves and physical constraints;
- structure canonicalization, duplicate tolerance, and symmetry handling;
- ranking thermodynamic quantity and reference state;
- search budget, discovery-rate/recurrence diagnostics, and termination rule;
- higher-level reoptimization and property validation of retained candidates.

Operational heuristic: run multiple independent searches and track the best
energy, number of new unique minima, motif/composition coverage, and recurrence
of low-energy families as a function of search effort. Repeated discovery
raises confidence but never proves the global minimum. Preserve the full
candidate lineage; do not report only the lowest structure.

Operational heuristic: reoptimize important low-energy candidates with an
independent higher-fidelity reference method and compare ordering, geometry,
forces, and relevant observables. A low G-NN energy alone is a model prediction,
not a confirmed phase.

## Plan reaction exploration

Separate these literature-described goals:

- SSW structure search seeks minima and can retain transition information along
  its trajectory;
- SSW-RS aims to identify low-energy pathways and explicitly locate transition
  states linking important minima;
- CBD/DESW are transition-state/pathway tools;
- ML-TS uses a known reaction map and constrained reaction coordinates while
  globally exploring surface structures;
- MMLPS combines parallel SSW-RS exploration with pathway filtering and
  microkinetic feedback to expand a reaction network.

The 2024 review describes SSW-RS in three conceptual stages: extensive pathway
collection, fast double-ended pathway screening, and DESW transition-state
search. Those concepts do not supply 3.7.3 commands or convergence settings.

Define the reactants/products, composition and environment, candidate reaction
space, TS/path acceptance tests, endpoint identity, frequency/connection
verification, barrier/free-energy convention, duplicate reaction rule,
network-growth metric, kinetic model, and stopping condition. Validate retained
paths and transition states with the declared reference method.

Operational heuristic: report reaction-network coverage and unresolved branches
instead of calling the lowest barrier found “the mechanism.” Independent search
branches, alternative surface structures, and competing pathways are part of
the uncertainty.

## Plan active learning and NN construction

The public architecture combines DFT calculations, SSW sampling, and NN
training in an iterative loop. Use the following evidence flow without assuming
LASP syntax:

1. define the target application and reference electronic-structure contract;
2. seed a diverse, provenance-complete dataset;
3. train a model with an independent validation/test design;
4. explore the target PES using SSW/MD/search appropriate to the application;
5. detect poorly described or domain-risk configurations;
6. compute new reference labels, quarantine failures, and add accepted data;
7. retrain under a new model/dataset identity;
8. stop only when predeclared domain, observable, and uncertainty criteria hold.

Operational heuristic: split data by parent trajectory/search cycle,
composition, structural family, or physical regime. Randomly mixing neighboring
SSW/MD frames across train and test sets can hide poor transferability.

Record energy/force/stress errors by relevant subset, not only a global RMSE.
Validate low-energy ordering, metastable/transition regions, dynamical
stability, and the final observables. Model disagreement is a risk signal, not
ground truth; close uncertain regions with independent reference calculations.

## Plan MD without inventing syntax

The review describes conventional NVE, NVT, and NPT capabilities plus enhanced
sampling with specifiable restraints. Public evidence does not establish the
3.7.3 keyword mapping, thermostat/barostat families, units, random-seed
behavior, output cadence, completion markers, or restart contents.

The scientific plan may still define target ensemble, state variables,
boundaries, time-step study, equilibration, production, observables, replicas,
uncertainty, drift/distribution checks, and model-domain validation. Mark every
value as project intent. Do not create a LASP input until the authorized manual
maps each intent to exact syntax.

## Attest opaque artifacts

For a user-supplied package/case that cannot be parsed here, retain only safe,
bounded metadata:

| Artifact | Required attestation |
|---|---|
| documentation | title/version/edition, source authority, access date, SHA-256, completeness, redistribution status |
| executable/package | edition, archive and binary hashes, acquisition authority, expiry/terms, platform/compiler/MPI closure |
| input | safe label/hash, claimed task, author/tool, matching manual section, no secret/private-path leakage |
| model/PES | hash, type, provenance, training/reference lineage, domain, rights |
| output | hash/size, exact producing run, process/scheduler state, authoritative format/marker mapping |
| state/restart | parent run/state hash, claimed retained fields, segment boundary, exact-continuation claim false until proven |
| trajectory | source hash, engine provenance, frame/site identity and units mapping from authorized documentation |

Never paste restricted manual text, proprietary model bodies, license tokens,
private calculation trees, or external-engine licensed contents into this
repository. A self-authored attestation cannot authenticate itself; use a
separately controlled manifest/signature for trusted evidence.

## Interpret performance and licensing

The author review reports particular LASP 3.7 CPU benchmarks and linear-scaling
implementations for G-MBNN training/evaluation. Those measurements use specific
systems, network architecture, atom counts, CPU hardware, MPI layout, and
memory conditions. They establish implementation context, not a universal
resource estimate for another model or workflow.

Operational heuristic: benchmark the exact authorized package on a bounded,
representative case while holding the scientific contract fixed. Record model,
atom count, neighbor/environment complexity, ranks/cores, CPU/runtime, wall
time, peak memory, and output cost. Never weaken search coverage, model
fidelity, validation, or acceptance criteria to reproduce a paper benchmark.

The public LASP Hub page reviewed on 2026-07-22 states:

- LASP `3.7.3-ac` is for academic testing and expires after one month;
- LASP `3.7.3-pro` has no expiration-time limit and advertises additional
  model/support/interface access;
- both list Linux and Intel MPI/Compiler 2017 or newer;
- the public launch examples are `Src/lasp` directly and through four-rank
  `mpirun`;
- manual/examples are advertised but require an authorized session;
- LASP GPUNN is no longer released or maintained on LASP Hub and is routed to
  LASPAI as a separate product.

These statements are not complete license or ABI terms. Treat software,
interfaces, NN models, external engines, datasets, and outputs as independent
rights objects. An academic-download label does not grant redistribution.

## Accept, weaken, or stop

Stop before input generation or execution when any of these is missing:

- authorized complete 3.7.3 manual/examples and exact package/edition terms;
- version/edition/build/environment and external-interface closure;
- exact syntax, units, defaults, output/failure markers, and restart contract;
- PES/model identity, domain validation, and lawful use;
- task-specific search/MD/training estimator and stopping rule;
- independent numerical/statistical/reference validation;
- explicit execution authority and a clean output/segment plan.

With public evidence alone, a valid result is a bounded scientific plan, an
opaque artifact inventory, and an exact evidence-gap list. It is never a
positive LASP completion, convergence, structure, mechanism, or model claim.

Primary public sources: the [LASP authors' 3.7 review](https://doi.org/10.1021/prechem.4c00060),
its [open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11672538/), the
[LASP Hub download route](http://www.lasphub.com/#/lasp/download), the authors'
[LASP overview](https://doi.org/10.1002/wcms.1415), and the primary
[SSW-NN material-discovery paper](https://doi.org/10.1039/C7SC01459G).
