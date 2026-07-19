# Environment and authorization boundary

## Local candidate

- Use Python 3.12 or a reviewed Python 3 interpreter; only the standard library is required.
- Run with `python3 -B` in an offline environment.
- Supply single-link regular non-symlink JSON files no larger than 4 MiB. The reviewed platform must support `dir_fd` operations for `open`, `stat`, `link`, and `unlink`, plus `O_DIRECTORY`, `O_NOFOLLOW`, `O_NONBLOCK`, `pread`, regular-file `fsync`, and directory `fsync`.
- Request/evidence bases remain bound by device/inode for one command. Lower path components may not be symlinks or change identity after binding; only a stable platform root alias is normalized.
- Use a pre-existing output directory; each command creates one new file through held-fd staging, no-replace hard-link publication, exact payload verification, and directory sync, and refuses overwrite or input aliases.

## Not authorized

The candidate does not authorize or perform browser search, DOI resolution, database access, article download, credential use, DFT execution, scheduler submission, repository writes outside the chosen output, external messaging, or publication.

A future source-retrieval adapter must be separately registered with network-read and license/terms gates. A future calculation handoff must produce an immutable plan/request and obtain a separate human execution-authorization decision. Scientific acceptance remains a later human decision over exact records.
