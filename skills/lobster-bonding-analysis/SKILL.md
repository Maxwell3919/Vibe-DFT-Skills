---
name: lobster-bonding-analysis
description: Plan and audit provenance-bound LOBSTER 5.1.1 basis projection, COHP, COOP, COBI, projected-DOS, population, and charge analyses from eligible plane-wave DFT parents; use when preparing a VASP/QE/ABINIT handoff, selecting basis functions, energy windows or bonds, mapping lobsterin/lobsterout and output files, checking spilling and curve conventions, or limiting bonding claims without trusting filenames or process exit alone.
---

# LOBSTER Bonding Analysis

This is a **development, non-routable Skill**. It provides deterministic planning and synthetic-fixture validation, but it does not activate LOBSTER, run the licensed binary, or establish chemical-bonding conclusions.

## Start here

1. Read [official-sources-and-version-strategy.md](references/official-sources-and-version-strategy.md), [official-sources.yaml](references/official-sources.yaml), and [version-matrix.yaml](references/version-matrix.yaml) before making a version, syntax, output-format, provider, or license statement.
2. Use [calling-and-recipes.md](references/calling-and-recipes.md), [practical-workflows.md](references/practical-workflows.md), [software-capability-catalog.json](references/software-capability-catalog.json), and [task-recipes.json](references/task-recipes.json) for public capabilities, parent/basis preparation, `lobsterin` review fields, output-role maps, manual-required native surfaces, handoffs, and failure semantics.
3. Use `scripts/lobster_catalog.py` to search the evidence catalog, emit a non-executing plan, or probe candidate executable names. Exact native argv and `lobsterin` syntax remain blocked without the authorized 5.1.1 manual/examples.
4. Read [fail-closed-contract.md](references/fail-closed-contract.md), select one task from [task-evidence-profiles.json](references/task-evidence-profiles.json), and run `scripts/lobster_guard.py` only on the declarative interchange.
5. Interpret findings through [finding-catalog.json](references/finding-catalog.json) and maturity through [maturity-matrix.json](references/maturity-matrix.json).
6. Treat [weak-model-decision-table.json](references/weak-model-decision-table.json) as the only machine routing source: evaluate ascending priority, select the first match, and use its evidence-free final default when no earlier case is established.
7. Check [environment-license-boundary.md](references/environment-license-boundary.md) before external execution. Never expose licensed binary/manual/example/basis bytes or private VASP artifacts.

## Supported candidate tasks

| Task | Deterministic surface | Current maturity | Maximum candidate claim |
|---|---|---|---|
| `projection-audit` | Parent identity, execution binding, basis identity, completion, absolute charge/total spilling | synthetic-validated | no positive claim |
| `cohp-audit` | Projection gates plus normalized synthetic COHP curve, energy zero, sign convention, integral consistency | synthetic-validated | no positive claim |
| `coop-audit` | Projection gates plus normalized synthetic COOP curve and integral consistency | synthetic-validated | no positive claim |
| `dos-audit` | Projection gates plus normalized synthetic total/projected DOS closure | synthetic-validated | no positive claim |
| `bonding-package-audit` | All preceding technical gates in one lineage-bound package | synthetic-validated | no positive claim |

VASP is the only parent route represented by a candidate fixture. Quantum ESPRESSO and ABINIT are documented LOBSTER inputs, but remain `design-only` here until provider/version-specific parent records and legally reusable real artifacts pass forward tests. A software name or a `WAVECAR`-like filename never establishes parent eligibility.

COBI/ICOBI, Mulliken/Loewdin populations and charges, site potentials, and
Madelung outputs are documented planning surfaces, not current deterministic
guard tasks. Review them through
[practical-workflows.md](references/practical-workflows.md) and the authorized
manual. Do not represent their absence from the guard as absence from LOBSTER,
or their appearance in a public parser as validated 5.1.1 format support.

## Non-negotiable gates

Keep these gates separate and fail closed:

- **authorization gate**: exact LOBSTER version, registered non-profit research entitlement, and non-redistribution boundary;
- **parent gate**: immutable DFT record hash, independently hash-bound parent-validation receipt, code/version/task/protocol, structure fingerprint, k-point/settings/potential-metadata hashes, wavefunction hash, completion and numerical gates;
- **execution-binding gate**: execution record binds the validation receipt, parent record, DFT protocol and input identities, input wavefunction, structure, and `lobsterin` hashes;
- **basis gate**: basis family, source, per-element orbital list, and parser-observed basis agree;
- **projection gate**: absolute charge and total spilling exist and meet user-declared thresholds, and projected-band fraction plus projection energy window/Fermi evidence are complete; no universal threshold is silently supplied;
- **artifact gate**: required files exist, are regular bounded files, and match declared SHA-256 values;
- **curve gate**: curve type, columns, energy unit/reference, spin representation, sign convention, finite values, monotonic energy grid, and declared integral semantics are explicit;
- **task gate**: every requested observable has its task-specific evidence;
- **claim gate**: technical curve validity remains distinct from bond strength, bond order, oxidation state, stability, mechanism, or causality.

Scheduler success, process exit zero, a completion phrase, low spilling, and a visually plausible curve are independent observations. None substitutes for the other gates.

## Deterministic CLIs

Search or plan from public evidence without launching LOBSTER:

```bash
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py search "projected COHP"
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py plan recipe.native-run
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py probe
```

Native and VASP recipes return exit `3` with `LOBSTER_AUTHORIZED_MANUAL_REQUIRED`; the QE route returns exit `3` as `design-only`. On 2026-07-19 no candidate executable was found, so native validation is `native-not-run`.

The guard uses only the Python standard library, accepts JSON only, never imports LOBSTER data as code, emits sorted JSON, and refuses outputs that alias any input. Request and evidence reads share one retained root directory descriptor; relative components are opened with no-follow `openat` traversal and special files are rejected without blocking. Reports use a same-directory fsynced staging descriptor plus atomic hardlink create-if-absent publication with post-publication inode, size, link-count, and payload verification. Every existing target and the compatibility `--overwrite` flag are rejected. It does not execute external programs.

```bash
python3 skills/lobster-bonding-analysis/scripts/lobster_guard.py plan \
  --request skills/lobster-bonding-analysis/examples/plan-request.json \
  --output lobster-plan-report.json

python3 skills/lobster-bonding-analysis/scripts/lobster_guard.py audit \
  --request skills/lobster-bonding-analysis/fixtures/audit-request-pass.json \
  --output lobster-audit-report.json
```

Stable exit codes:

| Code | Meaning |
|---:|---|
| `0` | Deterministic plan/audit passed at its declared candidate maturity |
| `2` | Unsafe, malformed, duplicate-key, privacy-bearing, or contract-invalid input |
| `3` | External authorization, real-artifact maturity, provider route, or expert evidence is missing |
| `4` | A declared artifact cannot be parsed under the selected version/fixture profile |
| `5` | One or more scientific-technical gates failed |

Every report contains `status`, `maturity`, `maximum_claim`, gate states, stable finding codes, content hashes, limitations, and minimal next actions. `passed` means only that the selected candidate-level deterministic checks passed.

## Interpretation boundary

- COHP and plotted `-COHP` use opposite signs. Never label bonding/antibonding regions until the stored convention is explicit.
- COHP, COOP, COBI, and DOS answer different questions; one cannot stand in for another. ICOBI is a basis- and convention-bound bond-index descriptor, not an automatic experimental bond order.
- Integrated values are bound to an energy window and Fermi reference. Curve and `lobsterout` references must agree without an after-the-fact shift; a number without both is not comparable evidence.
- Low charge spilling is necessary evidence for projection quality, not proof that the chosen basis is chemically complete or uniquely appropriate.
- Mulliken and Loewdin populations/charges are basis-partitioned descriptors;
  neither is an automatic oxidation-state assignment or a substitute for
  charge-density analysis.
- Relative bond-strength comparisons require comparable parents, basis families, structures, spin treatment, energy windows, interaction selectors, and numerical settings.
- No automated result from this candidate can declare a bond, bond order, oxidation state, phase stability, or causal structure-property mechanism. The strongest future automated state remains `eligible_for_expert_review`; human scientific acceptance is separate.

## Handoffs

On eventual promotion, consume a reviewed `electronic-wavefunction-source@1.0` and produce `normalized-dataset@1.0` plus `artifact-manifest@1.0`. Those shared interfaces are still planned for this route, so this candidate currently emits only its local validation report. Do not create substitute shared manifests or expose a postprocess route from the candidate directory.

Use `dft-postprocess` only after this Skill's parent, projection, selector, units, reference, and sign gates are preserved in the adapter handoff. Use `dft-campaign-efficiency` only for measured cost evidence; it must not relax projection or claim gates.

## Activation blockers

Promotion remains blocked until all of the following are independently reviewed:

- lawful private access to LOBSTER 5.1.1 and an authorization receipt that stores no credential or binary content;
- exact-byte/version evidence for the shipped manual and basis resources without redistributing restricted material;
- real VASP parent/output forward fixtures with redistribution permission, plus negative/truncated/version-drift cases;
- real QE and ABINIT provider profiles before those routes are supported;
- parser validation against genuine 5.1.1 `lobsterout`, COHP, COOP, and DOS artifacts, including spin and large-file cases;
- shared `electronic-wavefunction-source@1.0` schema and semantic binding;
- reviewed `dft-postprocess` adapter, full repository regression, weak-model blind tests, and an explicit atomic promotion decision.

The fixture inventory and legal origin are recorded in [fixture-manifest.json](references/fixture-manifest.json).
