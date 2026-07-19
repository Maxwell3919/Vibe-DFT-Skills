# Environment and license boundary

## Candidate-only planner and auditor

- Python 3.10 or newer is sufficient for the pure-standard-library CLI and tests.
- No LOBSTER, VASP, Quantum ESPRESSO, ABINIT, MPI, scheduler, plotting library, or network access is needed.
- Inputs are JSON plus bounded text fixtures. The tool performs no external execution.

## Real LOBSTER integration

- Provider identity: LOBSTER 5.1.1, first-party registered binary.
- First-party advertised targets: licensed distributions supplied by the provider; the repository environment profile currently recognizes Linux and Windows x86_64 only.
- Authorization: registered non-profit research license, non-exclusive, non-transferable, revocable, and non-redistributable.
- Private assets: binary, manual/examples when restricted, basis resources, and parent wavefunctions stay outside Git and outside reports.
- VASP parents additionally require a lawful VASP/POTCAR environment; no POTCAR content may enter this repository.
- QE/ABINIT parents require independent exact-version parent profiles before use.

An authorization receipt may record issuer, entitlement class, software version, validity state, and a privacy-safe receipt hash. It must not contain credentials, registration data, licensed bytes, personal details, or private installation paths.

## Execution separation

This candidate has no executor. Any future runner must be owned by the reviewed execution layer, use an explicit argv without a shell, default to dry-run, refuse overwrite, bind input/output hashes, separate scheduler/application/scientific state, and emit a privacy-safe execution record. Binary discovery or a zero return code cannot promote maturity.

## Redistribution

All committed fixtures are original synthetic text created for this repository. They contain no LOBSTER output excerpt, basis parameters, binary content, VASP potential content, or unpublished calculation result. Genuine regression fixtures require written redistribution permission or a validator that operates on private artifacts without committing them.
