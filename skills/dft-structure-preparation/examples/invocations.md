# Candidate invocation examples

Run all commands from this candidate directory. These examples exercise only local,
deterministic gates; they do not activate the candidate or invoke a DFT engine.

```bash
python3 scripts/structure_prepare.py audit fixtures/si-periodic.json
python3 scripts/structure_prepare.py roundtrip fixtures/si-periodic.json fixtures/si-wrapped-reordered.json
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation wrap
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation reorder --order Si-1,Si-0
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation supercell --repeat 2 1 1
python3 scripts/structure_prepare.py plan-export fixtures/water-molecule.json --target qe
python3 scripts/structure_prepare.py probe-backends
```

An audit can return exit `0` while reporting `requires-decision`; add
`--require-calculation-ready` when a downstream export requires readiness. Every current candidate
report remains `claim_ceiling=no_positive_claim`; `future_gate_ceiling` is not activation.
