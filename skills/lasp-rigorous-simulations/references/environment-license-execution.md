# Environment, license, and execution boundary

## Verified for this candidate

- Python 3.10+ standard library is sufficient for offline inventory.
- No LASP executable, scheduler, MPI/GPU stack, compiler, package manager, network, or credential is used.
- Author literature describes LASP 3.7 and points readers to the LASP Hub.
- The public LASP Hub download page reviewed on 2026-07-22 identifies LASP `3.7.3-ac` and `3.7.3-pro`, Linux, Intel MPI and Intel Compiler 2017 or newer, and executable `Src/lasp`.
- The same page gives direct `[LASP Installation DIR]/Src/lasp` and `mpirun -np 4 [LASP Installation DIR]/Src/lasp` examples, advertises a manual/examples, and distinguishes expiring academic and non-expiring professional editions.

Read [execution-and-executable-map.md](execution-and-executable-map.md) before discussing installation or execution.

## Still not verified

The public page is not a complete compatibility matrix. Exact CPU architecture, Intel compiler/runtime release compatibility, MPI ABI, libraries, Python dependencies, license mechanism, binary/source contents, environment variables, input/runtime files, output names, and resource expectations remain unknown here. Obtain them directly from an authorized version-matched distribution and review them before changing this candidate.

The public page provides access/edition statements, not complete software terms. Software use, redistribution, citation, interface, publication, and commercial restrictions remain unresolved. Treat the software as restricted until exact authorized terms are retained in a permissible authority record. Models, datasets, structures, and outputs have independent terms.

## Execution authority

This candidate grants none. A future execution layer must name the exact executable/hash, edition/expiry/license context, host, immutable inputs, working/output roots, resource envelope, command class, time window, and stop policy. No public side-effect-free version option was verified; do not invent `lasp --version` or run a discovered binary merely to probe it.

## Privacy

Use anonymous IDs and basenames. Exclude credentials, private paths, hostnames, usernames, scheduler identifiers, license tokens, unpublished results, and restricted model bodies.
