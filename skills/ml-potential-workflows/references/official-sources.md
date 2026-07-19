# Official-source boundary

Use version-matched first-party documentation. These locators justify only the stated
workflow distinction; they do not prove a local installation, model, dataset, result
or license.

| Provider | First-party locator | Bounded use |
|---|---|---|
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/training.html> | Distinguishes training, validation, independent test, checkpoint/restart and device choices. |
| MACE | <https://github.com/ACEsuit/mace/releases/tag/v0.3.16> | Registered release identity locator. |
| NequIP | <https://github.com/mir-group/nequip/releases/tag/v0.19.0> | Registered release identity locator; its breaking-change notes remain part of the exact environment boundary. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/configuration/data.html> | Documents data modules and train/validation/test split management. |
| NequIP | <https://nequip.readthedocs.io/en/latest/guide/configuration/config.html> | Documents ordered train/validation/test workflow roles. |
| NequIP | <https://nequip.readthedocs.io/en/latest/api/save_model.html> | Distinguishes checkpoints and packaged models and exposes path/compatibility boundaries. |
| FairChem | <https://pypi.org/project/fairchem-core/1.10.0/> | Registered FairChem v1 package identity used by the two legacy pretrained profiles; package identity alone does not identify a model. |
| FairChem | <https://pypi.org/project/fairchem-core/2.21.0/> | Registered FairChem v2 package identity used by the UMA profile; package identity alone does not identify a model or task head. |
| FairChem | <https://fair-chem.github.io/> | First-party documentation root; exact model/head/version pages must be resolved during provider promotion. |

Resolver rules:

1. Match exact provider and version to the environment registry.
2. Treat docs as documented behavior only.
3. Resolve pretrained model cards, artifact hashes and licenses independently.
4. If a decisive config, unit, task-head or packaging rule is absent from the selected
   version source, mark it unresolved.
5. Do not copy provider documentation, model weights or dataset samples into this
   candidate.
