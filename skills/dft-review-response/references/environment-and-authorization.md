# Environment and authorization boundary

- Use a reviewed Python 3 interpreter; Python 3.12 is the reference environment and only the standard library is required.
- Run offline with `python3 -B`.
- Inputs are single-link regular non-symlink JSON objects no larger than 4 MiB. The reviewed platform must support `dir_fd` operations for `open`, `stat`, `link`, and `unlink`, plus `O_DIRECTORY`, `O_NOFOLLOW`, `O_NONBLOCK`, `pread`, regular-file `fsync`, and directory `fsync`.
- Request/evidence bases remain bound by device/inode for one command. Lower components may not be symlinks or change identity after binding; only a stable platform root alias is normalized.
- The output parent already exists; the command creates one new file through held-fd staging, no-replace hard-link publication, exact payload verification, and directory sync, and refuses overwrite or input aliases.
- No DFT executable, scheduler, browser, mail client, journal portal, credential, or proprietary file is required.

Local planning, auditing, and JSON rendering are the only side effects. Manuscript editing, new calculation execution, external messaging, and submission require separate registered tools and explicit human authorization. Human scientific acceptance and release decisions must be separate content-addressed records resolved outside this candidate.
