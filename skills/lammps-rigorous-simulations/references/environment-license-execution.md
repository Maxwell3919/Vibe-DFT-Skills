# Environment, license, and execution boundary

## Offline audit

Python 3.10+ standard library is sufficient. No LAMMPS binary, MPI runtime, GPU stack, scheduler, network, or credential is used.

## Future authorized execution

Record exact release banner, executable SHA-256, source revision, installed packages/styles, compiler, MPI, FFT, accelerator suffix, Kokkos/GPU/OpenMP configuration, precision, processor layout, platform, environment variables, input closure hashes, resource limits, output destination, and known-issues review. Check `lmp -h`/configuration through a version-pinned adapter only after explicit authorization.

Authorization must name the software, executable, host, command class, immutable inputs, working/output roots, resource envelope, and time window. This Skill has no execution authority.

## Legal and privacy

Official LAMMPS documentation describes GPL version 2 distribution. Preserve source notices. Potential/model/plugin/data rights are independent; require source and license status for every artifact before redistribution or positive provenance claims.

Use anonymous IDs and basenames. Exclude credentials, hostnames, usernames, scheduler identifiers, private absolute paths, unpublished structures/results, and restricted model contents.
