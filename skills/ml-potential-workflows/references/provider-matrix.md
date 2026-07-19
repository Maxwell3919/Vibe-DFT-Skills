# Provider capability matrix

This matrix is a routing boundary, not proof that a package or model is available.

| Provider profile | Registered version | Candidate mode | Required future adapter evidence |
|---|---:|---|---|
| `mace-python` | MACE 0.3.16 | train/evaluate/package precursor | compatible Python/PyTorch matrix, exact config and CLI schema, legal dataset/model, restart and inference regression |
| `nequip-python` | NequIP 0.19.0 | train/evaluate/package precursor | compatible Python/PyTorch/Lightning/extensions, current config schema, checkpoint/package boundary, inference regression |
| `fairchem-v1-gemnet-oc` | FairChem 1.10.0 | pretrained evaluation precursor | exact model artifact/model card/license, task head, units, domain and evaluator regression |
| `fairchem-v1-equiformer-v2` | FairChem 1.10.0 | pretrained evaluation precursor | same evidence, with provider/model-specific architecture and task profile |
| `fairchem-v2-uma` | FairChem 2.21.0 | pretrained evaluation precursor | exact UMA task/head, model identity, license, units, domain and inference regression |

MACE/NequIP training plans and FairChem pretrained evaluation are different modes.
The generic auditor rejects a provider/mode pair outside the machine matrix in
`mlp_guard.py`. It does not translate configs between frameworks.

Framework import success is not model validation. Provider package license does not
grant model or dataset rights. A model version string without artifact SHA-256 is not
identity.
