# Candidate invocation examples

Run all commands from this candidate directory. These examples exercise only local,
deterministic gates; they do not activate the candidate or invoke a DFT engine.

```bash
python3 scripts/structure_prepare.py import-cif-manifest structure-manifest.json
python3 scripts/structure_prepare.py audit fixtures/si-periodic.json
python3 scripts/structure_prepare.py roundtrip fixtures/si-periodic.json fixtures/si-wrapped-reordered.json
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation wrap
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation reorder --order Si-1,Si-0
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation supercell --repeat 2 1 1
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation supercell \
  --matrix 1 1 0 0 2 0 0 0 1
python3 scripts/structure_prepare.py transform fixtures/si-periodic.json --operation strain \
  --deformation 1.02 0 0 0 1.02 0 0 0 1 --max-strain 0.03
python3 scripts/structure_prepare.py make-slab fixtures/si-periodic.json \
  --axis 2 --layers 4 --vacuum-ang 15
python3 scripts/structure_prepare.py build-interface substrate-slab.json film-slab.json \
  --max-repeat 6 --max-strain 0.05 --max-angle-deg 1 \
  --registry-shift 0.5 0.5 --gap-ang 2.5 --vacuum-ang 18
python3 scripts/structure_prepare.py site-edit fixtures/si-periodic.json \
  --operation insert --site-id Li-interstitial-0 --element Li --fractional 0.5 0.5 0.5
python3 scripts/structure_prepare.py site-edit fixtures/si-periodic.json \
  --operation substitute --site-id Si-1 --element Ge
python3 scripts/structure_prepare.py place-guest slab.json fixtures/water-molecule.json \
  --mode adsorbate --anchor-site O-0 --surface-frac 0.5 0.5 --height-ang 2.2
python3 scripts/structure_prepare.py place-guest porous-host.json fixtures/water-molecule.json \
  --mode host-guest --anchor-site O-0 --target-cart 5.0 5.0 5.0
python3 scripts/structure_prepare.py plan-export fixtures/water-molecule.json --target qe
python3 scripts/structure_prepare.py probe-backends
```

An audit can return exit `0` while reporting `requires-decision`; add
`--require-calculation-ready` when a downstream export requires readiness. Every current candidate
report remains `claim_ceiling=no_positive_claim`; `future_gate_ceiling` is not activation.
The slab and interface commands accept already normalized JSON, not raw CIF. Parse CIF with the
active `cif-structure-analysis` Skill first. Interface matching ranks bounded geometric candidates;
site insertion and guest placement require explicit coordinates and never certify stability.
