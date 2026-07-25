# CP2K official-source and version policy

## Source classes

- Use versioned pages under `https://manual.cp2k.org/` for documented input behavior, defaults, units, restrictions, tutorials, and troubleshooting.
- Use `https://github.com/cp2k/cp2k` only for exact emitted strings, implementation behavior, regression evidence, and provenance not stated in the manual.
- Treat project outputs, campaign experience, forum posts, third-party tutorials, and current analysis as separate non-official evidence classes.

## Version gate

1. Read `CP2K| version string:` from the audited output.
2. Normalize the stable version only when the output gives it explicitly, for example `2026.2`.
3. Build the matching manual root as `https://manual.cp2k.org/cp2k-<YEAR>_<MINOR>-branch/` or the equivalent historical numeric branch.
4. Do not use `trunk` for a stable release claim. `trunk` is development documentation and may differ from the released executable.
5. If the matching page is absent or cannot be live-verified, state: `Exact behavior for CP2K <version> is not verified by a matching official manual page.`
6. Use the changelog only for changes it explicitly documents.

## Resolver behavior

`references/official-source-registry.json` defines the curated decisive surface. `references/official-manual/index.json` inventories every page discovered from the stable branch `genindex.html`; `manifest.json` binds the registry, index and each mirrored page to SHA-256.

`scripts/resolve_official_sources.py` distinguishes:

- `cached_exact`: version, branch, registry, source URL, source-content hash and local snapshot hash all match the checked snapshot;
- `live_matches_cached`: a live HTTP 200 response has the exact registered final URL, a valid retrieval timestamp, and content bytes whose SHA-256 matches `cached_exact`;
- `live_changed_from_cached`: the exact official URL reopened, but its content hash differs from the checked snapshot;
- `live_unavailable_cached_exact`: the checked snapshot remains exact, but a requested live receipt was unavailable or malformed;
- `url_only`: the resolver constructed a registered URL but has no exact cached content;
- `unresolved`: the live content has no checked baseline or another identity requirement cannot be established.

Only `cached_exact` and a `live_matches_cached` result produced by the resolver in the current process can support a positive version-sensitive official claim, and both are bound to the checked-in source-content and snapshot hashes. A serialized bundle cannot prove that its self-declared live receipt was produced by a network retrieval: copied URLs, hashes, byte counts, status and timestamps are untrusted data. Legacy `cached_version_matched` or `live_verified` labels fail closed. `live_changed_from_cached`, `live_unavailable_cached_exact`, `url_only`, and `unresolved` support no positive claim.

Live retrieval records the exact final URL, HTTP status, retrieval time, byte count, and content SHA-256. It does not store the page. Reopen the cited page when answering a version-sensitive question, but never treat TLS success alone as content identity.

Claim packages must carry `pass_cached_exact` records. `validate_claim_package.py` independently reconstructs those records from the checked-in snapshot. Use its explicit `--live-replay` mode when the validation process itself must reopen every required URL and compare the returned bytes with the cached source hashes. Without that replay, a package that claims `pass_live_matches_cached` is blocked. No independent signed platform-attestation interface is currently implemented; do not promote a bundle receipt by schema, status, hash-shaped strings or timestamp syntax alone.

## Snapshot maintenance

Run `scripts/sync_official_manuals.py --refresh --version <VERSION>` to build the complete page index and curated snapshot in a temporary directory, then replace the old snapshot only after every page succeeds. Run `--check` offline to verify the registry hash, inventory hash, topic set, file set and every page hash. Never hand-edit generated snapshot pages.

## Search order

1. exact section/keyword page in the matching stable manual;
2. matching-version methods/getting-started page;
3. matching-version changelog;
4. official source code for exact output/implementation evidence;
5. unresolved, with the smallest missing source or runtime evidence.
