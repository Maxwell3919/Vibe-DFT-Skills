# Public community and browser-rendered source ingestion

Use this route only to preserve a public source for later review. It does not
turn a forum post into official software behavior, measured campaign evidence,
or a portable recommendation.

## Choose the least powerful retrieval route

Apply this order:

1. use a registered pinned receipt, source archive, provider API, or PDF;
2. use registered direct HTTP for a static public page;
3. use `crawl4ai-render-v1` only when JavaScript or browser rendering is needed;
4. block login-only, unregistered, robots-disallowed, private-network, or
   bypass-dependent sources.

Do not use stealth, proxy rotation, supplied cookies, credentials, custom
JavaScript, LLM extraction, screenshots, deep crawl, or cache reuse. Do not
work around a challenge page. A browser may execute the page's normal public
JavaScript only after the URL profile, DNS destinations, redirects, and
`robots.txt` pass.

The browser result is a derived navigation/rendering artifact. It cannot
replace the registered official source bytes or authorize version-sensitive
parameter claims.

## Use registered source scopes

Read `registry/document-fetch-adapters.yaml` through the atomic registry
snapshot.

- `official-software` requires an active authority from
  `registry/official-source-authorities.yaml`. Planned software remains blocked
  because its origin and version identity are unresolved.
- `official-package` is limited to the documentation profiles whose keys are
  checked against every normalized distribution in `requirements-dev.txt`.
  Bind the installed package version before using version-sensitive behavior.
- `public-community` is limited to the registered public profiles. It always
  carries evidence class `community-source-claim` and claim ceiling
  `source-claim-only`.

This is route coverage, not corpus completeness. A passing registry audit does
not prove that every manual page was retrieved, semantically sliced, current,
or applicable to the installed executable.

## Produce a bounded capture receipt

First record why the native route was insufficient. Create exactly one request:

```bash
python3 tools/crawl4ai_capture.py plan \
  --source-class public-community \
  --profile-id keinsci-public \
  --url '<REGISTERED_PUBLIC_URL>' \
  --fallback-condition javascript-required \
  --native-evidence '<PRIVACY_SAFE_NATIVE_OBSERVATION>' \
  --require-css '<TARGET_CSS_SELECTOR>' \
  --require-text '<TARGET_TOPIC_MARKER>' \
  --forbid-text '<KNOWN_ERROR_PAGE_MARKER>' \
  --out <OUTSIDE_GIT>/request.json
```

Run the optional exact-version browser environment and write the body outside
Git:

```bash
python3 tools/crawl4ai_capture.py capture \
  --request <OUTSIDE_GIT>/request.json \
  --output-dir <OUTSIDE_GIT>/capture
python3 tools/crawl4ai_capture.py validate \
  --manifest <OUTSIDE_GIT>/capture/manifest.json \
  --artifact-root <OUTSIDE_GIT>/capture
```

Exit `0` is a validated technical capture. Exit `3` is a deliberate block,
including missing or mismatched runtime, robots denial, unregistered scope, or
unsafe destination. Exit `4` is a browser/runtime failure. None of these exits
states whether a calculation recommendation is correct.

The request must include a target-specific CSS or Markdown content gate. A
nonempty challenge, login, redirect, or generic error page is a failed capture,
not a successful source. The manifest hash-binds the exact request, robots receipt, optional direct
response, rendered DOM, readable Markdown, adapter version, Playwright version,
browser version, and enforced controls. Response headers, cookies, credentials,
absolute paths, private host names, and source bodies are not copied into Git.

## Promote only through the experience evidence ladder

For each captured community claim:

1. quote or paraphrase only the minimal claim and retain its public URL;
2. record author/date/software/version/task scope when the page supplies them;
3. cross-check syntax and program behavior against version-matched official
   documentation;
4. list assumptions, risks, counterexamples, and a falsifier;
5. keep the claim outside `campaign-record` until actual private run evidence
   exists;
6. propose a one-change controlled pilot without changing scientific
   acceptance criteria;
7. promote only after comparable scientifically accepted campaign evidence.

Multiple posts repeating the same advice are still multiple source claims, not
independent calculation validation. A validated capture proves artifact
identity and policy compliance only.
