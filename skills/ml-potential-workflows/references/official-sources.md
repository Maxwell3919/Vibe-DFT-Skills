# Official-source boundary

Use version-matched first-party documentation. These locators justify only the stated
workflow distinction; they do not prove a local installation, model, dataset, result
or license.

| Provider | First-party locator | Bounded use |
|---|---|---|
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/training.html> | Distinguishes training, validation, independent test, checkpoint/restart and device choices. |
| MACE | <https://github.com/ACEsuit/mace/releases/tag/v0.3.16> | Registered release identity locator. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/evaluation.html> | Documents provider evaluation entry point; generic thresholds and split independence remain external. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html> | Rolling first-party model index for elements, datasets, theory, target, outputs and licenses; resolve exact artifacts separately. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/finetuning.html>, <https://mace-docs.readthedocs.io/en/latest/guide/multihead_finetuning.html> | Documents experimental naive/replay/LoRA and head-aware fine-tuning concepts; not an accepted generic provider mode by itself. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/lammps.html> | Documents a rolling LAMMPS route and warns about calculator comparison; exact 0.3.16 export remains blocked pending native validation. |
| NequIP | <https://github.com/mir-group/nequip/releases/tag/v0.19.0> | Registered release identity locator; its breaking-change notes remain part of the exact environment boundary. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/configuration/data.html> | Documents data modules and train/validation/test split management. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/configuration/config.html> | Documents ordered train/validation/test workflow roles. |
| NequIP | <https://nequip.readthedocs.io/en/latest/api/save_model.html> | Distinguishes checkpoints and packaged models and exposes path/compatibility boundaries. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/getting-started/workflow.html> | Documents restart, package, compile, target and artifact roles for the current workflow. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/configuration/model.html> | Documents model units and per-type energy shifts; exact installed config remains authoritative. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/training-techniques/fine_tuning.html> | Documents package-based fine-tuning, cutoff compatibility, and shift/scale modification. |
| NequIP | <https://nequip.readthedocs.io/en/latest/integrations/ase.html>, <https://nequip.readthedocs.io/en/latest/integrations/lammps.html> | Documents target-specific ASE/LAMMPS compilation, unit/type mapping, and rank boundaries. |
| FairChem | <https://pypi.org/project/fairchem-core/1.10.0/> | Registered FairChem v1 package identity used by the two legacy pretrained profiles; package identity alone does not identify a model. |
| FairChem | <https://pypi.org/project/fairchem-core/2.21.0/> | Registered FairChem v2 package identity used by the UMA profile; package identity alone does not identify a model or task head. |
| FairChem | <https://fair-chem.github.io/> | First-party documentation root; exact model/head/version pages must be resolved during provider promotion. |
| FairChem | <https://fair-chem.github.io/fairchemv1-v2/> | Establishes the v1/v2 breaking API and artifact boundary. |
| FairChem | <https://fair-chem.github.io/uma/> | Rolling official UMA task/DFT/charge/spin/domain boundary; a task name is not artifact identity. |
| FairChem | <https://fair-chem.github.io/fine-tuning/> | Documents current single-task UMA ASE-LMDB fine-tuning and `e`/`ef`/`efs` modes; current generic route remains blocked. |
| FairChem | <https://fair-chem.github.io/ase-calculator/>, <https://fair-chem.github.io/lammps/> | Documents current v2 inference/deployment surfaces; no local compatibility evidence follows. |
| UMA model card | <https://huggingface.co/facebook/UMA/blob/main/README.md> | Official gated model-card locator for checkpoint names/checksums/access/license boundary; bind exact downloaded SHA-256 separately. |

Resolver rules:

1. Match exact provider and version to the environment registry.
2. Treat docs as documented behavior only.
3. Resolve pretrained model cards, artifact hashes and licenses independently.
4. If a decisive config, unit, task-head or packaging rule is absent from the selected
   version source, mark it unresolved.
5. Do not copy provider documentation, model weights or dataset samples into this
   candidate.

Rolling MACE, NequIP and FairChem pages were reviewed on 2026-07-22 and are paired
with the exact registered release/tag sources in the machine catalogs. Installed help
and exact native fixtures must win if rolling docs drift.
