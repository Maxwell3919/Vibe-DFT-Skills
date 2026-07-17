# DFT Codex Skills

Private single-source repository for four maintainable Codex skills:

- `qe-rigorous-calculations`: official QE behavior, workflow design, input/output audit, and scientific convergence.
- `vasp-rigorous-calculations`: official VASP behavior, workflow design, strict input/output audit, and scientific convergence.
- `dft-postprocess`: deterministic QE/VASP extraction, tool routing, structured artifacts, and Python plotting.
- `dft-campaign-efficiency`: private campaign records and evidence-backed efficiency recommendations.

The calculation skills emit `run_manifest.json`. Postprocessing consumes run manifests and emits `artifact_manifest.json`. The efficiency skill consumes accepted run/artifact evidence and emits advisory `recommendation_record.json`; it never changes calculation inputs silently.

Canonical JSON contracts live under `contracts/`. Runtime databases, raw calculation outputs, licensed POTCAR data, private paths, hosts, and accounts must stay outside this repository.

## Validate

```bash
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

## Install

After source validation and explicit migration approval, preview symlink installation:

```bash
python3 tools/install_skills.py --dry-run
```

The installer refuses to overwrite existing real directories. Existing QE/VASP installed copies must be migrated deliberately after comparing and backing up their state.
