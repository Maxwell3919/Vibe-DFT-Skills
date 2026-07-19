# GROMACS environment, license, and execution boundary

## Environment evidence

Before a future real-artifact validation, capture without executing the simulation:

- exact GROMACS version and source/build commit;
- precision mode, compiler, CMake configuration, FFT library, SIMD, MPI/thread-MPI, GPU backend and external libraries;
- operating system, architecture, accelerator model/driver and rank/thread layout;
- exact TPR, MDP, processed topology, coordinate and checkpoint hashes;
- command argv and relevant GROMACS environment variables, especially any warning suppression or reproducibility option.

The planned registry profile targets GROMACS 2026.3 CPU. The current machine has no verified GROMACS executable; this candidate therefore performs only Python offline audit. Finding an executable is not activation evidence.

## License boundary

The GROMACS project describes the software as free software under LGPL-2.1-or-later. Preserve the applicable notice and source obligations when redistributing it. Treat every bundled or user-supplied force field, water/ion model, topology, plugin, library, parameter set, coordinate set and trajectory under its own terms. Record `license_status=verified|unresolved|restricted`; only `verified` can pass the redistribution gate.

Do not bundle real project inputs, checkpoint contents, restricted parameters, unpublished trajectories, credentials, hosts or accounts. The fixtures in this candidate are project-authored syntax artifacts, contain no GROMACS output copied from a run, have no scientific meaning, and are declared redistributable in `fixture-manifest.json`.

## Authorization boundary

This Skill does not authorize or implement:

- `gmx grompp`, `gmx mdrun`, `gmx dump`, `gmx check`, `gmx energy`, or any other external binary;
- local/remote process launch, scheduler submission, SSH, container launch or package installation;
- overwrite, deletion, modification or continuation of a calculation tree.

A future execution route must use argv, a new staging directory, explicit user authorization, exact executable/build identity, bounded resources, dry-run preview, immutable execution records, cancellation semantics, and separately audited output. Preprocessing and production runs require separate authorization receipts.

## Reproducibility boundary

GROMACS checkpoints retain full-precision state needed for continuation, but exact continuation depends on executable, hardware, libraries, rank layout and dynamic behavior. Record checkpoint SHA-256 plus parent run ID and treat a changed build/hardware/layout as a reproducibility boundary. `-reprod` is not a scientific-validation substitute and is not invoked here.
