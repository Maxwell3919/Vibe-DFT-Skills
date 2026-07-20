# Security Policy

## Scope

Security reports may concern:

- credential, token, SSH, hostname, account, scheduler, or private-path exposure;
- path traversal, symlink escape, hard-link aliasing, or bundle-root escape;
- command injection or unsafe subprocess construction;
- unauthorized local, remote, scheduler, or network side effects;
- lease, idempotency, cancellation, or recovery bypass;
- restricted scientific content such as POTCAR data entering Git or a release;
- malformed records that bypass evidence, privacy, lifecycle, or claim-ceiling gates;
- dependency or GitHub Actions supply-chain risks;
- release artifacts that expose development Skills as routable.

Scientific disagreements about convergence or methodology are normally handled as correctness issues. They become security issues when an implementation can bypass a declared blocker, fabricate evidence identity, exceed authorization, or expose restricted information.

## Reporting

Do not open a public issue containing a credential, private path, host, account, restricted artifact, exploit, or unpublished scientific result.

Use GitHub private vulnerability reporting or a private security advisory when that repository feature is enabled. Otherwise contact the repository owner through an established private channel and provide only the minimum information needed to reproduce the problem.

Include:

- affected commit, branch, release, Skill, tool, or contract;
- the expected boundary;
- the observed bypass or exposure;
- minimal reproduction steps using synthetic or redacted data;
- whether credentials or restricted files may already have entered Git history;
- whether the issue permits execution, modification, disclosure, or false evidence claims.

Do not attach real credentials, POTCAR contents, private calculation trees, unpublished numerical data, or real cluster configuration to the report.

## Initial response and containment

The maintainer should first determine whether the issue requires:

- disabling a workflow or release;
- removing a Skill from the active distribution;
- revoking a credential;
- freezing a lifecycle promotion;
- blocking a contract version;
- removing a release artifact;
- rewriting Git history after preserving an audit record;
- warning users that a baseline or maturity record is invalid.

Containment must not silently rewrite historical evidence. Affected records should be marked superseded, revoked, or blocked through a new auditable record.

## Disclosure boundary

A fixed version may be disclosed after:

1. the bypass or exposure has been reproduced;
2. affected credentials or artifacts have been contained;
3. regression tests fail on the vulnerable state and pass on the corrected state;
4. lifecycle, maturity, and release records have been reviewed;
5. any invalid scientific or engineering claim has been withdrawn or qualified.

## Supported versions

Until formal releases are published, only the current `main` branch is intended to receive security fixes. Whether that branch is protected is an external GitHub repository setting and must be verified separately. Historical commits and development branches are retained for audit and may remain unsupported.
