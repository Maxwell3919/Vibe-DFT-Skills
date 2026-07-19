# Task profiles and maturity

Evaluate each task, provider edition, exact version, and parent route independently. Overall
maturity is the minimum of invocation, parser, and scientific-validation axes.

| Route | Provider | Invocation | Parser | Scientific validation | Overall | Current claim | Future gate ceiling |
|---|---|---|---|---|---|---|---|
| XYZ/extxyz inventory | stdlib candidate 0.1.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Pipeline planning | stdlib candidate 0.1.0 | synthetic-validated | synthetic-validated | design-only | design-only | no_positive_claim | input_gates_only |
| Frame metadata execution | OVITO Basic 3.15.5 | synthetic-validated with API double | synthetic-validated | design-only | design-only | no_positive_claim | technical_run_gates_only |
| Coordination analysis | OVITO Basic 3.15.5 | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| Common-neighbor analysis | OVITO Basic 3.15.5 | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| Atomic strain | OVITO Pro 3.15.5 | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| Dislocation analysis | OVITO Pro 3.15.5 | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| Static rendering | conservative Pro 3.15.5 profile | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| Table export | OVITO Basic 3.15.5 | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |

The test API double proves only that authorization, import identity, selected frames, and result
serialization are wired. It is not an OVITO binary, real artifact, license, rendering, or numerical
reference test.

## Activation evidence still required

- Freeze and validate the shared pipeline contract and trajectory/structure adapters.
- Obtain a permitted Basic 3.15.5 environment and run exact-version real-tool tests on licensed,
  redistributable trajectories.
- Validate each modifier against independent numerical references, units, selectors, topology,
  mapping, PBC, cell, and frame conventions.
- Obtain external trusted OVITO Pro entitlement evidence before any Pro test; keep activation
  material private and separate from the repository.
- Validate render determinism or bounded nondeterminism, camera/color settings, image hashes or
  perceptual criteria, headless behavior, and visual QA.
- Add output artifact manifests and dft-postprocess adapter tests.
- Complete expert review and commit-aware registry/interface promotion.

Until then, keep the Skill in development at its registered `skills/` path and unroutable.
