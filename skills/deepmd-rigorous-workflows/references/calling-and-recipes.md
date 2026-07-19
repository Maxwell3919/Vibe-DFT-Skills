# DeePMD, dpdata, and DP-GEN calling boundary

The machine-readable [`workflow-catalog.json`](workflow-catalog.json) is the feature
index. [`workflow-recipes.json`](workflow-recipes.json) supplies concrete CLI/API
entry points, preconditions, expected outputs, restart rules, failure modes, units,
and scientific checks. Catalog discovery is read-only: every recipe is
`execution_authorized=false`, and the current native state is `native-not-run`.

## Route by requested operation

| Request | Provider entry point | Required distinction |
|---|---|---|
| Identify the installed provider/backend | `dp --version`, `dp --pt -h`, distribution metadata | Executable, Python distribution, backend and environment must agree |
| Generate the exact training schema | `dp --pt doc-train-input --out-type json_schema` | Regenerate for the exact installed version/backend; hash the output |
| Inspect descriptor neighbor counts | `dp --pt neighbor-stat ...` | Type order, systems, cutoff and periodicity are explicit |
| Train or restart | `dp --pt train input.json ...` | Training and restart are different lineage operations |
| Freeze/compress/test/deviation | Dedicated `dp --pt` subcommands | Every derived model is a new artifact and needs independent evaluation |
| Convert labeled data | `dpdata.LabeledSystem` / `MultiSystems` | Format parsing is not label comparability or split acceptance |
| Concurrent learning or property workflow | `dpgen run`, `init_bulk`, `simplify`, `autotest` | Scheduler/remote/DFT side effects require stage-specific authorization |
| LAMMPS inference | `pair_style deepmd` + ordered `pair_coeff` species | Engine units, type map, model domain, monitor and rollback are separate gates |

## Installation and version probe

The registered recipe is PyTorch CPU. The first-party install page distinguishes
this from the `deepmd-kit[cpu]` TensorFlow CPU extra. The documented PyTorch path
installs an appropriate PyTorch build first and then `deepmd-kit`; the recipe pins
DeePMD-kit 3.1.3 but deliberately does not invent a PyTorch version pin that the
selected provider page does not prescribe. A deployment environment must freeze the
actually resolved compatible lock.

After an authorized installation, capture all of:

```text
dp --version
dp --pt -h
python -c "import importlib.metadata as m; print(m.version('deepmd-kit'))"
```

Do not fall back to DeePMD's default TensorFlow backend when the plan says PyTorch.
The current host has none of the matching executables/distributions, so these probes
are recipes only and were not run.

## Typical DeePMD acceptance chain

1. Audit raw dataset provenance, units, type ordering, shapes, periodic boxes,
   group-disjoint train/validation/test/OOD roles, and source-calculation acceptance.
2. Capture the installed 3.1.3 PyTorch JSON Schema and validate the rendered config;
   do not treat provider defaults as scientific choices.
3. Run `neighbor-stat` over all relevant training systems, then justify and converge
   descriptor cutoff/selection.
4. Train with immutable input/data/environment hashes and explicit seeds. Treat
   non-finite loss, missing validation, data/config mutation, or partial checkpoints
   as failure.
5. Restart only from a bound checkpoint with an unchanged scientific plan. A changed
   dataset, type map, architecture, loss or backend is a new run.
6. Freeze to a new model, capture metadata, test every held-out frame (`--numb-test
   0`), report tail/slice/OOD errors, and compare compressed models independently.
7. Before MD, validate force/energy consistency, stable trajectories, conserved
   quantities where applicable, model-deviation monitoring, domain boundaries,
   fail-stop behavior and rollback.

Training completion or low aggregate RMSE does not establish transferability or MD
stability.

## dpdata and DP-GEN failure semantics

For dpdata, record the exact input format, parser/package identity, source ordering,
units, labels, atom/type ordering and output hashes. Rebuild into a new directory
after any input/type-map change. `deepmd/npy/mixed` is a storage format; it does not
make heterogeneous reference protocols comparable.

For DP-GEN, `param.json`, `machine.json`, provider executables, scheduler endpoints
and remote working directories are separate evidence. `run`, `init_bulk`,
`simplify`, and each `autotest` stage can create remote jobs or files. Partial or
ambiguous remote state blocks retry until reconciled; never infer stage completion
from a directory name. Active-learning selection must preserve rare/high-error
coverage and never tune against the held-out test/OOD result.
