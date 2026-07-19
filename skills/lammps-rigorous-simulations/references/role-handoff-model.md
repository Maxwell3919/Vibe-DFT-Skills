# LAMMPS role and handoff model

LAMMPS inputs are executable, so responsibility separation starts with code-surface review.

| Role | Primary responsibility | Handoff artifact |
|---|---|---|
| claim planner | bound task, units, observables and acceptance policy | no-execution plan |
| script-safety reviewer | reject dynamic code, expansion, unsafe includes and unknown commands | static safety inventory |
| build/model verifier | bind release, executable hash, styles, topology, pair model and terms | build and model closure |
| protocol reviewer | check integration ownership, ensemble, timestep, seeds, phases and restart limits | input-gate report |
| external authorizer | decide whether immutable inputs may run on a named environment | future lease outside this candidate |
| output/trajectory reviewer | check exact log segment, lost-atom policy, statistics, IDs, boxes and image flags | technical inventories |
| scientific reviewer | assess model domain, drift, finite size, replicas and uncertainty | external bounded decision |

Every handoff carries the prior report's exact raw-byte SHA-256, artifact hashes, warning/blocker list, `claim_ceiling=no_positive_claim`, `report_authenticity=unsigned-candidate-output`, and minimum next action. The self `report_fingerprint` is checked for consistency but is not a trust root. Only a separately verified trusted manifest/signature may attest report origin. No role may interpret a prior local pass as promotion or execution authority.
