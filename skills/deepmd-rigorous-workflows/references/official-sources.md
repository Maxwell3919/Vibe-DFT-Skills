# Official-source and backend boundary

Use first-party, version-matched sources only:

| Purpose | Locator | Bounded use |
|---|---|---|
| Installation/backend identity | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/install/easy-install.html> | Establishes documented installation/backend choices; not local availability. |
| DeePMD CLI/API surface | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/cli.html> | Documents explicit backend aliases and train, restart, freeze, compress, test, model-devi, neighbor-stat and schema commands. |
| Backend capabilities | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/backend.html> | Establishes version-matched backend names and that the documented training switch is limited to TensorFlow, PyTorch and Paddle; JAX/DP are not accepted by this training projection. |
| Training input | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/train/train-input.html> | Establishes the version-sensitive training-parameter source and provider schema-generation route. |
| Quick start and data roles | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/getting-started/quick_start.html> | Describes first-principles labels, training/validation data and a training workflow. |
| Release identity | <https://github.com/deepmodeling/deepmd-kit/releases/tag/v3.1.3> | Registered DeePMD-kit release locator. |
| DeePMD data format | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/data/system.html> | Documents system/type-map/array conventions used by provider recipes; metadata audit still does not inspect payloads. |
| DeePMD Python inference | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/inference/python.html> | Documents `deepmd.infer.DeepPot`; no model is loaded here. |
| DeePMD LAMMPS command | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/third-party/lammps-command.html> | Documents `pair_style deepmd` and species binding; it does not establish a safe deployment envelope. |
| dpdata release/system API | <https://github.com/deepmodeling/dpdata/releases/tag/v1.0.2>, <https://docs.deepmodeling.com/projects/dpdata/en/stable/systems/system.html> | Exact release identity plus rolling first-party API docs for `System`/`LabeledSystem`. |
| dpdata mixed format | <https://docs.deepmodeling.com/projects/dpdata/en/stable/formats/DeePMDMixedFormat.html> | Documents the mixed-type format; storage compatibility is not label comparability. |
| DP-GEN release/CLI | <https://github.com/deepmodeling/dpgen/releases/tag/v0.13.3>, <https://docs.deepmodeling.com/projects/dpgen/en/v0.13.3/overview/cli.html> | Exact release and CLI syntax for `run`, `init_bulk`, `simplify`, and `autotest`. |

The registry plans DeePMD-kit 3.1.3 CPU and records that `dp`, `dpdata`, `dpgen` and
their matching distributions are absent on the current machine. Public docs establish
behavior only. The dpdata pages are rolling and are paired with the exact 1.0.2
release; any version-sensitive ambiguity remains unresolved until installed help and
a native fixture agree. No source proves dependency compatibility, local package
identity, backend equivalence, data/model licenses or any result.

Do not copy provider documentation, tutorial data, checkpoints, models or logs into
the candidate. Synthetic metadata fixtures are independently written.
