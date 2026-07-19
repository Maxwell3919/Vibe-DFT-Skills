# Environment and authorization boundary

## Candidate runtime

- Python 3.10 or newer; standard library only.
- UTF-8 JSON inputs no larger than 1 MiB each.
- Offline execution with `PYTHONDONTWRITEBYTECODE=1` or `python -B`.
- No DFT executable, MPI runtime, scheduler client, SSH client, database, network access, credential, API token, pseudopotential, or licensed artifact is required.

The candidate CLI does not inspect the host environment, process environment, home directory, scheduler configuration, or remote filesystem. Logical labels are accepted; absolute host paths and secrets are not.

## Future integration prerequisites

Promotion requires reviewed adapters for the active operation-route registry, interface registry, environment profiles, bundle validators, and exact-byte record store. The adapter must pin compatible schema hashes and must fail closed on registry drift.

An execution-capable integration additionally needs all of the following outside this Skill:

1. A user-selected environment profile and scheduler profile.
2. Installed, version-identified, licensed software and pseudopotentials where applicable.
3. A staged immutable execution request whose inputs have verified hashes.
4. A separate human execution-authorization decision scoped to that exact request.
5. A deterministic issuer for a bounded, single-use, expiring execution lease.
6. An executor that enforces argv, resources, outputs, side effects, idempotency, recovery, and cancellation.

Credentials remain in the executor or approved secret store. They never enter workflow plans, prompts, fixtures, logs, reports, decisions, or leases.

## Human authorities

- The request owner may authorize the exact execution scope.
- A scientific expert may accept or reject an evidence-mapped scientific claim.
- A repository maintainer may promote the Skill and activate routes.

These authorities are distinct. A person or agent acting in one role does not implicitly gain the others.
