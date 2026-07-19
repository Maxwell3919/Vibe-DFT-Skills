# Fail-closed execution and evidence contract

## Gates

1. **Source gate** — require a strict object record, safe identifiers, a supported wavefunction format/suffix, producer method/version, ordered real elements, charge/multiplicity/electron state, basis/ECP declaration, and electron closure `sum(Z) - charge - ECP core electrons`.
2. **Wavefunction identity gate** — open the actual `--wavefunction` once as a bounded single-link regular file, stream its SHA-256, and require exact basename/hash/bytes identity before any plan or parse.
3. **Parent gate** — require raw parent record/input/output hashes, producer code/version, and independent input-validation, output-completion, electronic-convergence, and wavefunction-export passes. Recompute a canonical semantic projection that includes the raw record hash and all source semantics.
4. **Distribution gate** — require one exact version/platform profile. A community build, unknown banner, or cross-version menu reuse blocks.
5. **Planning gate** — emit a dry-run argv template, literal stdin tokens, required/forbidden sentinels, expected outputs, and limitations. Never execute the plan.
6. **Transcript gate** — require exactly one banner, exact update date, successful wavefunction load, main-menu sentinel, graceful termination, and no fatal/error sentinel.
7. **Artifact gate** — bind every parsed table to the audited source record and verified wavefunction; require finite values, stable dimensions, explicit method/unit, atom mapping, and charge closure. Parse only text returned by the verified read, never a second path read.
8. **Claim gate** — while the package is development/non-routable, every current report remains `no_positive_claim` with promotion/execution unauthorized. The lowest maturity among source, profile, transcript, parser, and fixture evidence bounds only `future_gate_ceiling`.

Weak-model routing consumes [weak-model-decision-table.json](weak-model-decision-table.json) as the only machine source of truth: select the first ascending-priority match and use its final evidence-free default when no earlier condition is established.

## State model

- `pass`: every requirement for the requested candidate check is satisfied.
- `blocked`: evidence or platform maturity is intentionally insufficient; exit 3 and identify the smallest next action.
- `fail`: supplied evidence is malformed, contradictory, unsafe, truncated, or outside contract; exit 2.

`completed`, `validated`, and `scientifically accepted` are distinct. A transcript may be complete while the input calculation or population analysis is scientifically unsupported.

Report publication is fail closed: reject existing/broken-link targets and every input identity; write, flush, and fsync a same-directory exclusive temporary file; atomically publish only if the target is absent; remove the temporary file on pre-publication failure. A failed write must not leave a target that resembles a complete report.

## Non-negotiable failures

- Duplicate JSON keys, BOM, NaN/Infinity, non-object roots, oversized/deep records, NUL text, or concatenated transcripts.
- Missing/invalid digest, actual-wavefunction identity mismatch, unsafe labels, inconsistent atom/electron metadata, absent parent hashes/gates, detached projection, or unrecognized wavefunction format.
- Unknown distribution, mismatched update date, repeated banner, missing prompt sentinel, fatal text, or absent graceful exit.
- Charge rows that are duplicated, non-contiguous, non-finite, element-mismatched, dimension-mismatched, or inconsistent with the declared total charge.
- Any attempt to infer source identity, method, energy reference, or scientific meaning from a filename or directory name.

## Privacy

Machine-readable output contains safe labels, hashes, counts, versions, and stable finding codes only. It never returns absolute paths or raw wavefunction contents.
