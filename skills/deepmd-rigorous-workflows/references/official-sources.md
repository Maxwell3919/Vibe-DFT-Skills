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
| NumPy/HDF5 system layout | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/data/data-conv.html> | Establishes root `*.raw`, `nopbc`, `set.*/*.npy`, HDF5 path, and raw-to-set boundaries. |
| Version-matched raw-to-set implementation | <https://github.com/deepmodeling/deepmd-kit/blob/v3.1.3/data/raw/raw_to_set.sh> | Establishes that the reference converter writes flattened NPY rows with `numpy.loadtxt`; it does not validate labels or conversion provenance. |
| Training and data roles | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/train/training.html> | Documents backend-specific training entry points and separate training/validation system summaries. |
| Learning-rate schedules | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/train/learning-rate.html> | Establishes 3.1.3 explicit start/stop requirements, exponential/cosine schedules, and warmup fields; no numeric choice is accepted as universal. |
| Fine-tuning | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/train/finetuning.html> | Distinguishes fine-tuning from restart and documents inherited model/type-map/energy-bias boundaries. |
| Freeze and compress | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/freeze/freeze.html>, <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/freeze/compress.html> | Establishes separate derived-artifact operations; not equivalence or acceptance. |
| Independent provider test | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/test/test.html> | Documents all-frame testing and detail output; not split independence or threshold validity. |
| Model deviation | <https://docs.deepmodeling.com/projects/deepmd/en/v3.1.3/test/model-deviation.html> | Defines committee force/virial deviation and absolute/relative outputs; not calibrated uncertainty. |
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

The exact DeePMD-kit 3.1.3 pages above were reviewed on 2026-07-22. This source review
does not replace a future installed CLI/schema probe or backend-specific native
fixture.
