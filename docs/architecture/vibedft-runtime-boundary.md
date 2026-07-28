# ADR: Separate the VibeDFT Skill plane from the runtime plane

- Status: Proposed
- Date: 2026-07-28
- Decision owners: repository maintainers
- Scope: Vibe-DFT-Skills and future VibeDFT execution components

## Context

The repository currently combines five concerns:

1. portable Agent Skills;
2. scientific and provenance contracts;
3. deterministic audit scripts;
4. official-document supply and cache metadata;
5. candidate orchestration and HPC execution designs.

The first four concerns are already useful without cluster access. The fifth requires durable process state, credentials, remote transports, scheduler adapters, recovery semantics, and native code execution. Keeping all five inside one source tree encourages three failure modes:

- an `active` Skill is mistaken for an installed and operational executor;
- a conversational agent becomes the implicit workflow database;
- scheduler or parser success is allowed to leak into scientific acceptance.

## Decision

Vibe-DFT-Skills remains the authoritative **Skill, policy, contract, and scientific-gate repository**.

Native execution is implemented in a separate, versioned **VibeDFT runtime package**. The runtime consumes released active-only Skill/contract artifacts and emits content-addressed records that are validated against this repository's interfaces.

The runtime may use an established process engine such as AiiDA or jobflow-remote through an adapter. The selected engine is an implementation detail and cannot redefine VibeDFT scientific gates, claim ceilings, or authorization boundaries.

## Ownership boundary

### Vibe-DFT-Skills owns

- Skill identity, lifecycle, routing metadata, and portable instructions;
- JSON Schema and semantic validators;
- official-source authority and receipt metadata;
- scientific decision tables and claim ceilings;
- synthetic fixtures and legally reusable real-artifact fixtures;
- promotion, activation, maturity, and release evidence;
- adapter capability declarations and supported-version ranges;
- deterministic validators that can run without private infrastructure.

### VibeDFT runtime owns

- process execution and checkpointing;
- local/SSH transport and scheduler interaction;
- credential references and site-profile resolution;
- immutable attempt creation and idempotency keys;
- execution leases and side-effect authorization enforcement;
- application process observation and terminal-state classification;
- restart and bounded recovery execution;
- durable event, artifact, and provenance persistence;
- plugin loading and adapter invocation;
- cancellation and post-cancellation observation.

### Code adapters own

- exact native executable command construction;
- input materialization from validated plans;
- supported executable/build ranges;
- native output parsing and restart ancestry;
- code-specific error detectors and bounded corrections;
- real-artifact integration fixtures;
- mapping native facts into VibeDFT contracts without raising claim ceilings.

## Contract flow

```text
workflow-plan
  -> human decision-record
  -> execution-request
  -> single-use execution-lease
  -> immutable attempt
  -> native execution events
  -> execution-record + run-manifest
  -> artifact-manifest / postprocess evidence
  -> convergence and physical-validity gates
  -> separate human scientific decision
  -> postdecision claim-evidence map
```

Each arrow is hash-bound. Later records may reference earlier records but may not rewrite them.

## Side-effect rule

No Skill text, parser result, scheduler state, or model output grants side-effect authority.

A runtime action that performs remote write, scheduler submit/control, external publish, or destructive deletion requires:

- an active and routable action;
- a contract-valid request;
- an exact, unexpired, single-use lease;
- matching subject, resource, environment, and side-effect scope;
- an idempotency key;
- a durable pre-action event;
- a post-action observation or explicit unknown-outcome state.

Unknown submission or cancellation outcomes block repetition until reconciled.

## Scientific rule

Runtime completion supports only execution facts. It cannot establish numerical convergence, physical validity, mechanism validity, superconducting interpretation, or publication readiness.

Scientific validators consume immutable execution evidence and emit separate bounded findings. A human decision or an explicitly authorized scientific decision service consumes those findings. The runtime stores the decision but does not create its authority.

## Site profiles

Private hostnames, accounts, paths, partitions, QoS values, module commands, and credentials remain outside this repository. Public schemas and anonymized fixtures define their shape.

A site profile resolves at runtime to:

- transport adapter;
- scheduler adapter;
- executable identities;
- launcher and environment setup;
- scratch and staging policy;
- resource limits;
- privacy classification.

Changing a site profile cannot silently change the scientific plan.

## Packaging

The deterministic runtime and validators should be published as installable Python packages with:

- `pyproject.toml` metadata;
- supported Python versions;
- locked CI/release environments;
- stable console entry points;
- optional extras for engines and code adapters;
- semantic versioning for public interfaces;
- signed or hash-verifiable release artifacts.

Portable Skill directories remain separately distributable through the active-only artifact.

## Pilot choice

The first pilot should target one QE host and one scheduler path. The decision between AiiDA and jobflow-remote should be based on a measured spike covering:

- remote submit/observe/cancel;
- checkpoint/restart behavior;
- provenance queryability;
- plugin complexity;
- recovery policy isolation;
- installation and maintenance cost on Talos;
- ability to preserve VibeDFT contracts without duplicating engine state.

Do not implement multiple engines before one pilot closes the full evidence path.

## Consequences

Positive consequences:

- the public Skill repository remains portable and privacy-safe;
- execution state is durable and queryable;
- code/scheduler integrations can mature independently;
- active lifecycle no longer implies native execution;
- scientific gates remain independent of infrastructure success;
- existing contracts and validators are reused rather than replaced.

Costs:

- an additional package and release process;
- adapter compatibility testing;
- schema migration and engine-to-contract mapping;
- operational deployment on Talos and approved compute hosts.

## Rejected alternatives

### Keep all execution logic inside Skill directories

Rejected because Skill source is not a durable process engine and repository-relative scripts do not provide transport, credential, scheduler, checkpoint, or provenance guarantees.

### Store campaign state in Git

Rejected because active calculation trees, private paths, credentials, mutable scheduler states, and high-frequency events do not belong in the public source-of-truth repository.

### Let the model orchestrate directly through shell commands

Rejected because conversational state does not provide idempotency, leases, durable events, unknown-outcome reconciliation, or stable scientific claim boundaries.

### Build a new general workflow engine first

Rejected because mature workflow engines already cover remote execution, scheduling, checkpointing, and provenance. VibeDFT's differentiating work is the scientific contract and validation layer.

## Migration

1. restore canonical activation/maturity evidence for current active Skills;
2. harden terminal-intent routing so non-routable Skills cannot be selected;
3. package current deterministic tools without changing their semantics;
4. define runtime plugin and event-store interfaces;
5. implement one QE SCF/relax adapter and one scheduler path;
6. add one real-artifact end-to-end fixture;
7. implement the QE two-dimensional phonon/EPC route;
8. promote adapters only after real execution, parser, recovery, and scientific-boundary evidence passes review.
