# Fail-closed menu and table contract

## Gates

1. **Parent gate** — require a raw VASP record SHA-256 plus a matching canonical evidence projection over raw hash, identity, code/version, structure, completion, spin, four independent acceptance gates, and sorted role/hash/bytes/label records. Require all four gates to pass.
2. **Binary gate** — require exact profile, platform, version banner, package/executable digest, and current usage-agreement evidence. This candidate plans but never executes.
3. **Menu gate** — bind an execution-independent `adapter_request` to one exact task profile, literal stdin tokens, ordered prompts/completion sentinels, required inputs, expected outputs, and a fresh-directory/no-overwrite policy.
4. **Transcript gate** — require separate post-run `adapter_evidence` with exactly one banner, one echoed task token, one echoed default token, ordered sentinels, and no fatal/error marker or repeated concatenated run.
5. **Artifact gate** — require actual `BAND.dat` and `KLABELS` hashes/bytes to equal the adapter evidence record.
6. **Energy/table gate** — bind `source_role: DOSCAR` and its projected hash, require the default-token input reference `vaspkit-default-fermi-zeroed`, explicit `eV`/`additive` semantics, finite rectangular rows, at least two ordered path coordinates with nonzero interval, one declared spin channel, and valid ordered high-symmetry labels.
7. **Claim gate** — keep current `claim_ceiling: no_positive_claim`, `promotion_authorized: false`, and `execution_authorized: false` for every status. Record the lowest possible post-promotion ceiling only as `future_gate_ceiling`.

Weak-model routing consumes [weak-model-decision-table.json](weak-model-decision-table.json) as the only machine source of truth: select the first ascending-priority match and use its final evidence-free default when no earlier condition is established.

## Failure semantics

- Exit `2` for malformed, contradictory, truncated, concatenated, hash-mismatched, unit/reference-ambiguous, or dimensionally invalid evidence.
- Exit `3` for unknown maturity, unsupported task/layout, incompatible platform, or absent version-specific protocol evidence.
- Exit `0` only for the requested candidate technical gate.

Never infer the VASP task, spin layout, Fermi reference, menu id, or version from a directory/file name. Never silently switch to native VASP parsing, a different VASPKIT task, or a third-party plotter. Never reopen a verified artifact path for parsing; parse the exact bytes read and hashed from one file descriptor.

## Privacy

Reports contain safe labels, hashes, counts, versions, menu tokens, normalized numbers, findings, and limitations. They omit absolute paths, host/account names, raw VASP files, and private working-directory text.
