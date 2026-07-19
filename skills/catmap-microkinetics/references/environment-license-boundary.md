# Environment and license boundary

## Safe planner/auditor

- Python 3.10 or newer; Python standard library only.
- No CatMAP, NumPy, SciPy, ASE, mpmath, Matplotlib, gmpy, compiler, MPI, scheduler, or network is required.
- No external program is executed and no native CatMAP artifact is loaded.

## Pinned real provider

- CatMAP v0.4.1 from the first-party release tag.
- Conservative repository profile: isolated Python 3.10 or 3.11; later Python versions require a fresh dependency/integration profile.
- Tag-pinned dependency lock for NumPy, SciPy, ASE, mpmath, Matplotlib, and any selected optional acceleration package.
- Record exact Python, package, source revision/tree hash, solver configuration, and dependency lock hash.
- GPL-3.0-only obligations apply to redistributed CatMAP source or derivative code. Input data, DFT energetics, thermochemical databases, and generated artifacts require separate provenance and redistribution review.

The candidate code is original and does not copy CatMAP code. It can audit declarations without CatMAP installed.

## Native artifact prohibition

Do not give an untrusted `.mkm`, CatMAP `.log`, `.py`, `.pkl`, or `.pickle` file to an agent or generic Python interpreter. A future trusted exporter must run only in a reviewed isolated environment on authorized inputs, serialize a strict declarative artifact, and bind it to an execution record. Import success or file readability is not a safety or scientific gate.

## Execution separation

Any future executor belongs to the shared execution layer. It must use explicit argv, no shell, dry-run by default, no overwrite, bounded resources, network policy, input/output hashes, and separate scheduler/process/solver/scientific states. This candidate does not auto-install CatMAP or dependencies.
