# Fail-closed contract

## Safe input boundary

Only bounded UTF-8 JSON objects are accepted. Native CatMAP `.mkm` setup files and log files can contain Python-oriented configuration or reload behavior; output data may be stored as pickle. The candidate therefore rejects `.mkm`, `.log`, `.py`, `.pkl`, and `.pickle` inputs, never calls `eval`/`exec`, never imports CatMAP, never unpickles data, and never launches a child process.

JSON is parsed with duplicate-key, UTF-8 BOM, and non-finite-number rejection. The request parent descriptor is retained as the evidence root; every relative directory component is traversed with `openat(O_DIRECTORY|O_NOFOLLOW)`, and the final component is opened once with `O_NONBLOCK|O_NOFOLLOW` and read only through that descriptor. Pre/post `fstat` is bound to anchored and lexical final `lstat` evidence, including device, inode, size, modification/change time, and link count. Inputs must be bounded single-link regular files, and their bytes, root, intermediate directories, and final path identity must not change while read. Reports contain hashes and labels, never resolved private paths, hosts, accounts, job IDs, or credentials.

Every successfully read request/evidence identity remains in process memory through output installation. Lexical/resolved path and device/inode comparisons reject output=request, output=artifact, symlink aliases, and hardlink aliases. Existing targets are never overwritten; the compatibility `--overwrite` flag fails closed. A retained private same-directory staging descriptor is fully written, reread for payload-hash verification, and fsynced. Publication uses `os.link` as atomic create-if-absent, validates both names and the retained descriptor in the transient two-link state, retires the private name, and rechecks the final single-link inode, size, and payload before directory fsync. Late target creation is never overwritten, and failed staging or publication leaves no accepted report.

## Candidate-local artifacts

The request binds three original declarative artifacts:

- `network`: species composition, phase, site occupancy, site capacities, and reaction stoichiometry;
- `thermochemistry`: units, reference state, conditions, per-species free energies, corrections/provenance, and forward/reverse barriers;
- `result`: provider/model hashes, solver branch and multiple-initial-state evidence, steady-state points, active-site rate normalization, disjoint data partition, sensitivity block, and uncertainty block.

These are candidate-local contracts, not the planned shared interfaces.

## Gate table

| Gate | Pass evidence | Fail or block condition |
|---|---|---|
| provider | exact v0.4.1 identity and expected synthetic/real environment state | unknown version, source drift, unsupported Python/dependency profile |
| safety | JSON-only regular bounded inputs | native executable/pickle format, link, traversal, private path, secret field |
| lineage | declared and observed artifact hashes agree; result repeats network/thermochemistry hashes | hash mismatch or detached result |
| network | unique IDs, defined references, finite integral stoichiometry, elemental and site balance | unknown species, imbalance, empty network |
| units | explicit supported energy, temperature, pressure, coverage, and rate basis | missing, mixed, or unsupported unit/reference |
| thermochemistry | complete finite free energies, provenance, conditions, and barrier-cycle closure | missing species, negative barrier, inconsistent reverse barrier |
| solver | exact solver/settings/branch, finite residual at/below predeclared tolerance, and enough initial-state trials with recomputed final-coverage fingerprints and bounded spread | self-reported convergence only, non-convergence, absent residual, post-hoc tolerance, detached or competing stored branches |
| coverage | bounded coverages and per-site capacity closure including empty sites | negative/overfull coverage or site closure failure |
| rate | finite elementary rates, supported active-site normalization, and species production residual at/below tolerance | unsupported rate basis or inconsistent steady-state production |
| sensitivity | method/scales/selectors/units explicit; all required perturbations converged | one-scale, failed perturbation, missing coefficient or selector |
| uncertainty | distribution/provenance/sampling identity and sample accounting explicit; intervals ordered | missing correlation/provenance, insufficient samples, convergence loss, invalid intervals |
| data partition | disjoint calibration/evaluation IDs, zero overlap accounting, and matching canonical partition hash | overlap, false accounting, or detached partition hash |
| claim | result is no stronger than task evidence and maturity | automatic mechanism/RDS/ranking/experiment claim |

## Status and exit mapping

- `passed` / `0`: selected synthetic candidate checks pass.
- `invalid_input` / `2`: safety or contract failure.
- `blocked_external_evidence` / `3`: provider integration, real-artifact maturity, unsupported mode, or expert claim is missing.
- `parse_failed` / `4`: a safe declared JSON artifact cannot be interpreted by its selected contract.
- `failed` / `5`: parseable evidence fails a network, thermochemistry, convergence, sensitivity, uncertainty, or lineage gate.

Priority is invalid input, parse failure, failed gate, then external blocker.

The canonical weak-model routing policy is [weak-model-decision-table.json](weak-model-decision-table.json), validated as shared `candidate-decision-table@1.0`. It is the only machine source of truth: select the first ascending-priority match and use the final evidence-free fail-closed default when no earlier condition is established. Passing the multi-start case does not prove global steady-state uniqueness.

## Claim ceiling

At current development/non-routable maturity, every report is capped at `no_positive_claim`, including synthetic passes. A real-artifact request remains blocked even when its declarative numbers pass, because no accepted v0.4.1 tool integration fixture exists. A future promoted implementation may at most emit `eligible_for_expert_review`; only a separate human decision record can establish scientific acceptance.
