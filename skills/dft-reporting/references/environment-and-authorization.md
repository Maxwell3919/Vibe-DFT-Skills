# Environment and authorization boundary

## Candidate environment

- Python 3.12 or another reviewed Python 3 version with only the standard library is sufficient.
- Run offline with `PYTHONDONTWRITEBYTECODE=1` or `python3 -B`.
- Inputs must be single-link regular non-symlink JSON files no larger than 4 MiB. The platform must provide reviewed `dir_fd` support for `open`, `stat`, `link`, and `unlink`, plus `O_DIRECTORY`, `O_NOFOLLOW`, `O_NONBLOCK`, `pread`, regular-file `fsync`, and directory `fsync` semantics.
- Request, evidence, plan, audit, and output bases are retained by device/inode during one command. Lower path components may not be symlinks or change identity after binding; only a stable platform root alias such as the macOS `/var` alias is normalized.
- The output parent must already exist. The CLI creates one new JSON file by held-fd staging and no-replace hard-link publication, verifies the exact payload before and after linking, syncs directory metadata, and refuses overwrite or any path/inode alias with an input.
- No DFT executable, scheduler, remote host, browser, network credential, document converter, or proprietary potential is required.

## Side effects

The only candidate side effects are local Python execution and creation of one new caller-selected JSON artifact. Planning, auditing, and rendering do not authorize calculation execution, external source retrieval, human review, email, repository mutation, submission, or publication.

Any future PDF/DOCX/LaTeX renderer must be a separately registered adapter with version, argv, input/output hashes, font and license provenance, failure semantics, deterministic fixture tests, and explicit local-write authorization. Any future send or publication adapter must require a separate human `external-publication` or `release` decision and is not part of this candidate.
