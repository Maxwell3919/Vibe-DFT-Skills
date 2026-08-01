# Controlled Crawl4AI source ingestion

## Decision

Vibe-DFT-Skills uses Crawl4AI as an optional, single-page browser-render
fallback. It does not replace the existing Git, provider API, direct HTTP, PDF,
or official-manual cache routes and it is not a bulk mirror engine.

This boundary keeps two useful properties separate:

- native routes preserve exact upstream bytes and version/source identity;
- browser rendering can expose public JavaScript-dependent content for
  discovery and review.

Rendered HTML and Markdown remain derived. Community content remains a source
claim. Neither is sufficient evidence for numerical convergence, physical
validity, scientific acceptance, or a portable efficiency rule.

## Registered coverage

`registry/document-fetch-adapters.yaml` is part of the atomic registry
snapshot. It binds:

- exact Crawl4AI release `v0.9.2` and commit
  `7e801521428ee12509994d39151006f64055ebe3`;
- one active single-page adapter and its two versioned interfaces;
- public community URL profiles for the calculation-chemistry forum and the
  Materials Science Community Discourse;
- official documentation entry points for every normalized distribution
  derived from `requirements-dev.txt`;
- native-first selection, outside-Git body storage, robots, network, identity,
  and claim-ceiling policies.

Registered calculation and planned scientific software continue to come only
from `registry/software-registry.yaml`. Active official sources must resolve
through `registry/official-source-authorities.yaml`; planned providers stay
metadata-only until their reviewed activation. Therefore “registry coverage”
must never be reported as “all official documents complete”.

Validate the coverage without network access:

```bash
python3 tools/document_fetch_adapters.py
python3 tools/interface_registry.py
```

## Isolated optional runtime

Keep the browser stack out of the core `.venv` and outside the repository:

```bash
python3 -m venv <OUTSIDE_REPOSITORY>/crawl4ai-0.9.2
<OUTSIDE_REPOSITORY>/crawl4ai-0.9.2/bin/python -m pip install \
  -r requirements-crawl4ai.txt
<OUTSIDE_REPOSITORY>/crawl4ai-0.9.2/bin/python -m playwright install chromium
<OUTSIDE_REPOSITORY>/crawl4ai-0.9.2/bin/python \
  tools/crawl4ai_capture.py check-runtime
```

The direct dependency is exact-pinned. Each successful manifest additionally
records the observed Playwright and Chromium versions. Transitive dependency
bytes and the browser executable are not vendored in Git; reproduce or compare
a capture using the manifest identities and the isolated environment receipt.

## Agent protocol

An Agent must:

1. route the scientific task to an active, routable Skill and read its required
   references;
2. resolve software, version, executable, task, and exact topic before source
   acquisition;
3. try registered native routes first and record the bounded failure or
   rendering gap;
4. create a `web-source-capture-request@1.0` for one registered URL;
   include a target-specific CSS or Markdown gate so a nonempty challenge,
   login, redirect, or generic error page cannot pass;
5. keep captures outside Git and accept only a validated
   `web-source-capture-manifest@1.0`;
6. use official browser output only as discovery/render evidence until exact
   official bytes and version identity are bound;
7. label community content as a source claim and cross-check it against
   official documentation;
8. keep execution authorization, scientific gates, and human acceptance
   separate from document access.

Discovery may identify candidate URLs through a provider API, static index, or
human-selected forum page. The Crawl4AI adapter itself forbids deep crawling,
so a discovery result cannot silently expand into a domain-wide scrape.

Validation is semantic as well as structural. It cross-binds the deterministic
request and record identities, canonical artifact paths and roles, adapter
configuration, registered final URL, HTTP 2xx status, captured robots bytes and
delay, replayed content gate, outside-Git directory, and absence of
unmanifested files. Schema-invalid manifests and requests stop before semantic
interpretation, and request parsing plus content-gate replay consume the single
hash-verified byte snapshots instead of rereading mutable paths.

## Security and failure semantics

The adapter rejects credentials in URLs, explicit ports, fragments, duplicate
query keys, unregistered origins/paths/queries, local or non-global addresses,
unsafe redirects, unavailable or disallowing robots policies, existing output
directories, and outputs inside the Git worktree. A Playwright route guard
checks main-frame navigation against the selected profile and blocks
non-public subresource destinations.

The SDK still executes public-site JavaScript in a local browser. DNS rebinding,
browser-engine vulnerabilities, and upstream content changes remain residual
risks; use an unprivileged isolated environment with no secrets and no access
to private research storage. This adapter does not provide an authentication,
anti-bot bypass, archival license, or external trust service.

## Storage and rollback

Only contracts, registries, tests, and synthetic fixtures belong in Git. Public
source bodies, request/capture instances, browser caches, and campaign
experience databases stay outside Git. Removing the optional environment and
capture directory rolls back runtime materialization without changing source
authority or scientific records. Removing the registered adapter requires a
reviewed registry/interface/routing migration; historical manifests remain
valid evidence for the version that produced them.
