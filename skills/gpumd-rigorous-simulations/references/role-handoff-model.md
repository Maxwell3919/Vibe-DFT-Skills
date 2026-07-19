# GPUMD role and handoff model

The model separates rolling-document risk, GPU environment evidence, potential provenance, run-block semantics, and scientific review.

| Role | Responsibility | Required handoff |
|---|---|---|
| claim planner | declare task, units, phase and uncertainty intent | no-execution plan |
| release/source verifier | match v5.3 tag, commit, bundled docs and known corrections | pinned source record |
| potential/state auditor | bind model.xyz, potential, license, PBC/cell and seed/restart state | input closure |
| run-block auditor | check propagating versus non-propagating controls and cadence | deterministic input report |
| GPU execution authorizer | independently verify licensed executable and supported CUDA/ROCm environment | future external lease |
| output/trajectory auditor | verify stdout, 18-column thermo and extxyz time/site/cell integrity | technical inventories |
| scientific reviewer | assess model domain, timestep/drift, size, replicas and statistics | external bounded decision |

Handoffs carry the exact raw-byte SHA-256 of every upstream report, descriptive self-fingerprints, artifact hashes, version/license gaps, current no-positive claim and minimum next action. Every candidate report is explicitly unsigned. A later role may add evidence but cannot erase an earlier blocker without a new audited record, and it must not treat a self-fingerprint as producer authentication. Evidence status requires an external trusted manifest or signature maintained outside this candidate's control.
