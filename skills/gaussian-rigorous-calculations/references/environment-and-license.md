# Environment and license boundary

## Registered target

- Provider profile: `gaussian-g16-c02`
- Expected identity: Gaussian 16 Rev C.02 Apple M-Series
- Runtime probe: external manual attestation only
- License class: restricted proprietary
- Redistribution: prohibited
- Repository maximum: development, offline validation

The public C.02 platform list dated 2025-03-18 names Apple M-series macOS 12-15.
The recorded current host is Darwin arm64 on macOS 26.5.2, outside that published
range. `g16`, `g09`, `formchk`, and `cubegen` were not found, so no help, version,
conversion, or calculation probe was attempted. This is `native-not-run`, not an
installation failure claim.

The profile is not a promise that Gaussian is installed, licensed, supported on the
current host, or executable. The deterministic probe validates only the shape and
declared values of an attestation supplied by a trusted platform; it does not discover
software or authenticate a license.

## Required external evidence before execution

1. A trusted provider identity and exact revision fingerprint.
2. A license/entitlement attestation issued outside the model response.
3. A supported operating-system and architecture record.
4. Exact executable identity kept private by the platform.
5. Exact input hash and resource request.
6. Human/platform execution authorization scoped to one action.
7. Private work/scratch directory policy and retention policy.
8. A post-run execution record that binds the exact plan/input/output identities,
   exit status, and checkpoint identity.

Missing any item blocks execution. None can be self-authored by the same model that
requests the run.

## Repository exclusions

Do not commit Gaussian executables, licensed documentation, license receipts,
activation data, full logs from private projects, checkpoint/formatted-checkpoint
files, scratch files, molecular structures without redistribution permission, or
environment dumps. Synthetic fixtures must be independently written and contain only
the minimal parser sentinels needed for tests.
