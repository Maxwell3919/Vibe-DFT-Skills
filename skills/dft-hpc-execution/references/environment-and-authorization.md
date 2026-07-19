# Environment, scheduler, license, and authorization requirements

## Candidate runtime

- Python 3.10 or newer, standard library only.
- Offline, `python -B`, no writable cache required.
- Input records are regular non-symlink UTF-8 JSON files no larger than 1 MiB.
- No Slurm/OpenPBS client, MPI, DFT code, SSH, network, cluster account, credential, container runtime, module system, or licensed file is needed.

## Real executor prerequisites after promotion

An external reviewed executor must establish and record:

1. Environment profile: OS/architecture, Python, MPI/library ABI, modules/containers, executable version/hash, pseudopotential/basis provenance, and license status.
2. Scheduler profile: family and version, cluster/site identifier as a privacy-safe label, command capability, resource syntax, accounting availability, job-ID grammar, state mapping version, and cancellation policy.
3. Storage profile: privacy-safe working label, staging roots enforced outside records, quota, scratch lifetime, output collection, hash verification, no-overwrite behavior, and cleanup authority.
4. Authorization: exact request decision, requested side effects, scope, validity, resource ceiling, and a fresh single-use lease.
5. Safety: argv-only invocation, no shell, no credential serialization, idempotency key, bounded timeout/output, recovery journal, cancellation reconciliation, and immutable execution record.

Site partitions, accounts, reservations, QoS, queues, projects, modules, launchers, GPU topology, filesystem paths, and allocation policy must come from reviewed profiles. The Skill must never invent them.

## Software and license boundary

The scheduler clients may be open-source, but DFT executables, pseudopotentials, basis sets, postprocessing tools, and cluster services have independent licenses and access controls. A valid scheduler plan does not establish permission to use or redistribute any scientific software or data. License evidence stays in the environment/software registries; licensed payloads and credentials stay outside Skill fixtures and reports.

## Authorities

- Human request owner: execution authorization for the exact bounded request.
- Deterministic lease issuer: derives a non-broadening single-use lease from that approval.
- External executor: performs only the leased action and records outcome.
- Scheduler/site administrator: site policy and account control.
- Scientific expert: scientific acceptance; never inferred from executor authority.
- Repository maintainer: Skill promotion and route activation.
