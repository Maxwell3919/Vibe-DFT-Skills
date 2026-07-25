# Task profiles and maturity

Maturity is route-, provider-, version-, and parent-specific. Compute the overall level as the
minimum of invocation, parser, and scientific-validation axes. Never aggregate a stronger route
into a weaker one.

| Route | Provider | Invocation | Parser | Scientific validation | Overall | Current claim | Future gate ceiling |
|---|---|---|---|---|---|---|---|
| CIF manifest import | candidate 0.2.0 + repository JSON Schema | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Audit normalized structure | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Wrap/reorder | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| General integer supercell / bounded strain | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Lattice-axis slab / vacuum | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Coherent oriented-slab interface | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Explicit interstitial/removal/substitution | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Explicit adsorbate / host-guest placement | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| Round-trip comparison | stdlib candidate 0.2.0 | format-fixture-validated | format-fixture-validated | synthetic-validated | synthetic-validated | no_positive_claim | input_gates_only |
| DFT export planning | stdlib candidate 0.2.0 | synthetic-validated | synthetic-validated | design-only | design-only | no_positive_claim | input_gates_only |
| pymatgen structure mutation | pinned wrapper/core | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |
| RDKit molecular mutation | pinned RDKit | design-only | design-only | design-only | design-only | no_positive_claim | documented_behavior_only |

The bundled fixtures are synthetic and do not raise scientific-validation maturity to real-artifact
or tool-integration levels. The declared symmetry in a fixture is test data, not independent
crystallographic evidence. The construction routes demonstrate deterministic geometry and
lineage only; they do not validate a surface termination, stable interface, defect site,
adsorption site, host-guest pose, or DFT relaxation outcome.

## Activation evidence still required

- Validate upstream CIF-to-snapshot and downstream shared-contract adapters on immutable bundles.
- Pin and test both pymatgen distributions on supported platforms; resolve wrapper/core version
  identity and serialization regressions.
- Pin and test RDKit sanitation, aromaticity, stereochemistry, conformer, charge, multiplicity,
  and serialization boundaries on isolated chemistry fixtures and real artifacts.
- Add real periodic and molecular artifacts with redistribution permission.
- Validate arbitrary-Miller slab, termination, interface, automatic defect/interstitial,
  adsorption-site, and host-void provider adapters separately before claiming those broader
  capabilities.
- Add code-format writer/parser round trips for every target and preserve atom order and units.
- Perform expert scientific review and commit-aware registry/interface promotion.

Until every condition is met, leave the candidate path null and routability false in registries.
