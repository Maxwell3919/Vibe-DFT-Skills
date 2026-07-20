# Lifecycle Promotion Policy

## Purpose

This policy defines the evidence required to change a Skill or software identity from `planned` to `development` or from `development` to `active`.

Lifecycle state is a repository routing decision. It is separate from software installation, environment availability, native execution, numerical convergence, physical validity, and scientific acceptance.

## Allowed transitions

```text
planned -> development -> active
```

Direct `planned -> active` promotion is prohibited.

Demotion is allowed when evidence becomes invalid, a security boundary is bypassed, a supported version becomes stale, a license boundary changes, or the active distribution cannot preserve fail-closed behavior.

## Planned to development

A planned identity may become development only when all of the following are present:

1. a canonical Skill or software identifier;
2. an explicit source path using the repository naming convention;
3. a concise `SKILL.md` with capability and non-capability boundaries;
4. declared side-effect classes;
5. declared consumed and produced interfaces;
6. version-matched primary-source provenance or an explicit blocker;
7. deterministic offline positive, negative, and blocked fixtures;
8. fail-closed routing and handoff behavior;
9. privacy and license classification;
10. a registered activation checklist.

Development status does not permit installation, routing, action execution, handoff, maturity claims, or positive scientific claims.

## Development to active

A development Skill may become active only through a dedicated pull request containing an immutable activation evidence record.

The evidence record must identify:

- Skill ID;
- candidate source commit;
- promoted source commit or pull request;
- Skill source-tree SHA-256;
- contract and registry digests;
- supported software versions, executables, tasks, observables, backends, and platforms;
- unsupported and untested scope;
- primary-source provenance;
- deterministic test report;
- positive, negative, blocked, and mutation fixtures;
- legally reusable real-artifact evidence when required;
- native execution evidence when claimed;
- privacy and license review;
- interface and lineage review;
- side-effect and authorization review;
- maintenance and forward-test plan;
- explicit human approval.

## Activation checks

The following checks are mandatory unless a stricter profile adds more:

1. identity and routing;
2. primary-source provenance;
3. capability boundary;
4. deterministic gates;
5. lineage and hashes;
6. scientific gate separation;
7. shared interfaces;
8. side-effect boundary;
9. idempotency, recovery, and cancellation where applicable;
10. validation evidence;
11. privacy and license;
12. portability and environment;
13. maintenance and forward testing.

A check may be marked not applicable only with a written justification reviewed in the promotion pull request.

## Scientific evidence boundary

Promotion to active may establish that a repository route is installable and callable for a defined scope. It does not automatically establish:

- that the required scientific software is installed in a user's environment;
- that every upstream software feature is supported;
- that a completed run is numerically converged;
- that a numerically converged run is physically valid;
- that a physical interpretation is scientifically accepted;
- that a result transfers to other materials, versions, platforms, or task types.

The maturity scope must therefore be queryable at least by:

```text
Skill x software x software version x executable x task x observable x backend x platform
```

## Promotion pull request

A promotion pull request must contain only the promotion and directly required evidence or corrections. It must state:

- exact promoted scope;
- exact excluded scope;
- evidence bundle identity;
- claim ceiling before and after promotion;
- side effects enabled by promotion;
- installation and routing impact;
- privacy and license result;
- rollback and demotion procedure;
- unresolved risks.

The implementation author must not be the sole source of scientific acceptance. Final promotion requires explicit owner approval.

## Automatic review and demotion triggers

Active maturity must be marked `review-required`, `stale`, or `blocked` when any of the following changes:

- software major or minor version;
- executable or output format;
- parser or normalization logic;
- contract major version;
- fixture bytes or provenance;
- backend;
- unit or reference-energy semantics;
- dependency major version;
- official-source authority;
- privacy or redistribution terms;
- authorization or side-effect behavior.

An invalid activation record, missing source-tree hash, failed mandatory regression test, or restricted-content exposure blocks distribution immediately.

## Evidence retention

Promotion evidence must remain available after activation. Active registry entries may have no incomplete activation requirements, but they must reference the immutable activation record that justified promotion.

Historical activation records must not be deleted or rewritten. Corrections require a superseding record.
