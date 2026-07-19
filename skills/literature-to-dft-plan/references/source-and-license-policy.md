# Source and license policy

- Do not fetch a source in the candidate CLI. A future retrieval adapter must declare network-read, terms, authentication, response status, exact-byte hash, version, and failure semantics.
- A DOI, URL, title, abstract, search result, or citation string is identity metadata, not content evidence.
- Treat non-synthetic real sources as requiring an `official-source-record@1.0` ref and external authority resolution.
- Require a source version for version-sensitive official software behavior. Do not project a current manual backward.
- Store only citation labels, identifiers, locators, hashes, and limitations. Do not embed licensed article text or restricted manual/potential content.
- `known-restricted` or `unknown` may still permit metadata-only citation planning, but never implies redistribution.
- Synthetic fixtures are explicitly non-scientific and may test structure only.
