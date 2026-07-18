# DFT Codex Skills

Private single-source repository for maintainable DFT and structure-analysis Codex skills:

- `qe-rigorous-calculations`: official QE behavior, workflow design, input/output audit, and scientific convergence.
- `vasp-rigorous-calculations`: official VASP behavior, workflow design, strict input/output audit, and scientific convergence.
- `cp2k-rigorous-calculations`: official CP2K behavior, fail-closed Quickstep audit, and evidence-linked convergence.
- `siesta-rigorous-calculations`: official SIESTA behavior, fail-closed FDF/pseudopotential audit, and evidence-linked convergence.
- `dft-postprocess`: deterministic extraction, tool routing, structured artifacts, and Python plotting; adapter maturity remains code- and observable-specific.
- `dft-campaign-efficiency`: private campaign records and evidence-backed efficiency recommendations.
- `cif-structure-analysis`: deterministic CIF facts, projections, symmetry attempts, and nearest-neighbor bond-length matching.

The calculation skills emit `run_manifest.json`. Postprocessing consumes run manifests and emits `artifact_manifest.json`; native QE/VASP adapters are implemented, while CP2K/SIESTA routes remain explicitly maturity-gated until real-artifact forward tests exist. The efficiency skill starts from privacy-safe case narratives, can normalize stable run/artifact evidence into campaign records, and emits advisory recommendations; it never changes calculation inputs silently.

Canonical JSON contracts live under `contracts/`. Runtime databases, raw calculation outputs, licensed POTCAR data, private paths, hosts, and accounts must stay outside this repository.

The canonical calculation-code and skill discovery interface is `registry/software-registry.yaml`. See `docs/integration-and-extension-plan.md` for software, calculation-capability, postprocessing-adapter, and contract-version extension rules; the dated repository audit is under `docs/repository-audit-2026-07-18.md`.

## Validate

```bash
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

## Install

After source validation and explicit migration approval, preview symlink installation:

```bash
python3 tools/install_skills.py --dry-run
```

The installer refuses to overwrite existing real directories. Existing installed copies must be migrated deliberately after comparing and backing up their state.
