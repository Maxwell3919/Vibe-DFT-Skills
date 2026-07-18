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

- `cached_version_matched`: version, branch, registry and page hashes match the checked snapshot;
- `live_verified`: the exact page was reopened successfully over verified TLS;
- `url_only_not_live_verified`: the resolver constructed a URL but has no matching cached/live content.

Cached text supports documented behavior only as of its recorded retrieval time. A URL-only result supports navigation but not a positive version-sensitive official claim.

Live retrieval records the final URL, HTTP status, retrieval time, and content SHA-256. It does not store the page. Reopen the cited page when answering a version-sensitive question.

## Snapshot maintenance

Run `scripts/sync_official_manuals.py --refresh --version <VERSION>` to build the complete page index and curated snapshot in a temporary directory, then replace the old snapshot only after every page succeeds. Run `--check` offline to verify the registry hash, inventory hash, topic set, file set and every page hash. Never hand-edit generated snapshot pages.

## Search order

1. exact section/keyword page in the matching stable manual;
2. matching-version methods/getting-started page;
3. matching-version changelog;
4. official source code for exact output/implementation evidence;
5. unresolved, with the smallest missing source or runtime evidence.
