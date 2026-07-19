# Low-reasoning decision table

The only machine source of truth is [weak-model-decision-table.json](weak-model-decision-table.json), validated against shared `candidate-decision-table@1.0`. This Markdown is human guidance only; the JSON wins on any difference. Select the first ascending-priority match, and use its final fail-closed default when no earlier condition can be established.

Use this table literally. Stop at the first failing gate. Never execute VASPKIT from this candidate, and never convert a pass into a scientific, execution, or promotion claim.

| Observation | Deterministic gate or finding | Exit | Allowed statement | Smallest next action |
|---|---|---:|---|---|
| `record_sha256` or `evidence_projection_sha256` is absent or malformed | `VK_SOURCE_INVALID` | 2 | Parent identity is not auditable | Export both lowercase SHA-256 fields from the accepted VASP record |
| Raw parent hash changes while the stored projection does not | `VK_PARENT_EVIDENCE_MISMATCH` | 2 | Raw record and selected semantics are detached | Rebuild the projection from the same accepted raw record; do not edit a digest by hand |
| Record id, code/version, structure, completion, spin, gate, or file role/hash/bytes/label changes without a new projection | `VK_PARENT_EVIDENCE_MISMATCH` | 2 | Parent semantics were mutated after projection | Regenerate the canonical projection and independently review the changed parent |
| Any of `input`, `output`, `electronic`, or `band_task` is not `pass` after a valid projection | `VK_PARENT_ACCEPTANCE_FAILED` | 2 | Parent VASP calculation is not accepted for this route | Repair and re-audit only the failed VASP gate |
| A task-required role is absent | `VK_REQUIRED_INPUT_MISSING` | 2 | Menu working set is incomplete | Supply the missing role with exact label, hash, and byte count |
| Energy `source_role` is not `DOSCAR`, or `source_sha256` differs from the projected DOSCAR | `VK_ENERGY_REFERENCE_INVALID` | 2 | Fermi lineage is unbound | Copy the accepted DOSCAR role hash into the energy-reference record |
| Energy unit/sign is not exactly `eV`/`additive` | `VK_ENERGY_REFERENCE_INVALID` | 2 | Energy transform is ambiguous | Express the transform as `energy_output = energy_input + additive_offset_ev` in eV |
| The route sends default token `0` but `input_table_reference` is not `vaspkit-default-fermi-zeroed` | `VK_ENERGY_REFERENCE_INVALID` | 2 | Default Fermi-zero route is contradicted | Correct the declared input reference or create a separately validated non-default menu profile |
| Parent declares two spin channels with a freshly valid projection | `VK_SPIN_LAYOUT_UNSUPPORTED` | 3 | Spin-polarized table layout is unsupported | Add a versioned two-channel fixture and parser contract before use |
| Exact profile is unknown | `VK_PROFILE_UNKNOWN` | 2 | Binary/menu identity is unknown | Select a registered exact version/platform profile |
| Exact profile exists but remains design-only | `VK_PROFILE_BLOCKED` | 3 | Version-specific route lacks maturity evidence | Add private exact-version transcript and package/binary digests |
| Official feature, tutorial, and task-number evidence conflict | `VK_DOCUMENTATION_CONFLICT` | 3 | No task number may be generated | Capture the exact installed banner/help/menu label/prompts/outputs and resolve the conflict |
| Task is only feature-listed, has no recipe, or is `official-feature-only` | `VK_RECIPE_NOT_ESTABLISHED` | 3 | Catalog listing only | Establish required files, every prompt token, outputs, and failures before making a plan |
| Unattended execution is requested but the recipe is interactive, contains placeholders, or lacks a complete exact-version prompt sequence | `VK_NONINTERACTIVE_NOT_ESTABLISHED` | 3 | Interactive documentation plan only | Resolve placeholders and validate the full stdin/output contract in a scratch copy |
| Task id is outside `211` or `252` | `VK_TASK_UNSUPPORTED` | 3 | Requested menu task is unsupported | Add a separate task profile, fixtures, and negative tests |
| Banner differs, repeats, or identifies another version | `VK_VERSION_MISMATCH` | 2 | Transcript does not prove the requested version | Capture one clean invocation from the exact binary |
| Task/default token or ordered prompt sentinel is missing or reordered | `VK_PROMPT_DRIFT` | 2 | Versioned menu protocol is not proven | Recapture stdin echo plus merged output; do not infer completion |
| Fatal/error marker appears in the transcript | `VK_FATAL_SENTINEL` | 2 | Invocation failed textually | Fix the first reported runtime/input failure and rerun privately |
| Transcript, `BAND.dat`, or `KLABELS` bytes differ from declared hash/size | `VK_ARTIFACT_HASH_MISMATCH` | 2 | Artifact lineage is broken | Re-hash the exact immutable artifacts and rebuild one source record |
| Band or label table is nonnumeric, nonfinite, ragged, unordered, or out of range | `VK_BAND_TABLE_INVALID` or `VK_KLABELS_INVALID` | 2 | Table normalization failed | Correct or recapture the smallest invalid artifact; do not plot it |
| Report target exists, is a broken symlink, or identifies an input | `VK_OUTPUT_EXISTS` or `VK_OUTPUT_INPUT_ALIAS` | 2 | No report was published and prior bytes were preserved | Choose a new output basename outside all input identities |
| Temporary write, file sync, atomic link, cleanup, or directory sync fails | `VK_OUTPUT_WRITE_FAILED` | 2 | Durable publication was not established | Preserve the original evidence, fix storage, and write to a new absent target |
| All requested candidate gates pass | no finding; lifecycle lock remains active | 0 | Only that the candidate technical gate passed; `claim_ceiling` remains `no_positive_claim` | Preserve the report and seek explicit reviewed promotion before any positive route claim |

Every report must retain `promotion_authorized: false` and `execution_authorized: false`. `future_gate_ceiling` describes only a possible ceiling after a separate promotion review; it is not current authority.
