# CP2K official-manual html2md refresh contract

## Pinned converter

The generated Markdown uses
[`helloworld-Co/html2md`](https://github.com/helloworld-Co/html2md) at Git
commit `ca08965af93e6565806a79087868daa439565ffc`. The upstream project exposes
conversion in a Nuxt component rather than a CLI. The local
`scripts/html2md_adapter.js` loads the project's installed `turndown` and
`turndown-plugin-gfm` dependencies and provides a stdin/stdout-only adapter.

Install the pinned project outside this repository:

```bash
git clone https://github.com/helloworld-Co/html2md.git \
  "${XDG_DATA_HOME:-$HOME/.local/share}/html2md"
cd "${XDG_DATA_HOME:-$HOME/.local/share}/html2md"
npm install --omit=dev --ignore-scripts
```

Do not expose the legacy Nuxt server merely to refresh documentation. Its
dependency tree is old and the refresh path needs only the local conversion
libraries. Set `HTML2MD_ROOT` or pass `--html2md-root` when the checkout is in
another location.

Verify the exact installation before fetching:

```bash
node scripts/html2md_adapter.js --identity
```

The adapter rejects any other upstream commit. The generated manifest records
the upstream commit, project version, exact conversion-library versions,
adapter schema, and adapter SHA-256.

## Extraction and conversion boundary

`sync_official_manuals.py` performs these steps for every registered page:

1. fetch only HTTPS content below the exact CP2K manual authority;
2. decode the response as strict UTF-8 and reject replacement characters;
3. select `article`, `main`, or the Sphinx `role="main"` document;
4. remove scripts, styles, navigation, forms, hidden presentation nodes, and
   the private-use Sphinx heading-link glyph;
5. resolve links and image sources against the exact page URL;
6. convert the bounded main-content HTML through the pinned html2md
   Turndown/GFM stack;
7. preserve TeX text, code-block text and indentation, definition signatures,
   subscripts, and superscripts with explicit adapter rules;
8. remove presentation-only space and tab characters at line ends without
   changing visible characters, indentation, or inline spacing;
9. prepend source URL, raw SHA-256, converter identity, and cached-source
   limitations.

Removing the heading-link glyph is a presentation repair, not a deletion of
manual prose. Edit links and substantive main-content text remain.

## Quality gates

Each page must pass all of the following before staging can replace the prior
snapshot:

- valid UTF-8 in source and Markdown;
- no Unicode replacement character;
- no Sphinx private-use heading-link glyph;
- every Unicode word token from cleaned official text remains in the same
  order in Markdown;
- every non-ASCII non-whitespace character from cleaned official text occurs
  at least as many times in Markdown;
- Markdown token count is not smaller than source-text token count;
- nonempty output with an exact source/hash/converter provenance header.

The manifest stores the source-text hash, character and token counts,
non-ASCII count, and the result of each quality gate. These checks detect
character loss and gross conversion damage; they do not prove typography in
every renderer. Manually inspect representative parameter, tutorial,
math/code, table/image, and changelog pages after each refresh.

## Transaction and verification

Run:

```bash
python3 scripts/sync_official_manuals.py --refresh --version 2026.2
python3 scripts/test_skill_scripts.py
python3 scripts/sync_official_manuals.py --check
```

Every fetch and conversion completes inside a staging directory. Any fetch,
identity, UTF-8, conversion, or quality failure leaves the prior validated
snapshot in place. Do not hand-edit generated pages.
