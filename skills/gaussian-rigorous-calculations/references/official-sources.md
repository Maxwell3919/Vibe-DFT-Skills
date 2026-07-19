# Official-source boundary

The source boundary is version-sensitive and intentionally narrow. These public,
first-party Gaussian pages are locators, not bundled manuals or proof that a local
installation is licensed.

| Purpose | First-party locator | Bounded fact used here |
|---|---|---|
| Product identity and revision boundary | <https://gaussian.com/g16/>, <https://gaussian.com/relnotes/> | Gaussian 16 is the product family; the revision notes identify C.02. |
| Input and route grammar | <https://gaussian.com/input/>, <https://gaussian.com/route/>, <https://gaussian.com/link0/> | Establishes ordered input sections, blank-line termination, route syntax, and Link 0 vocabulary. |
| Unix entry points and environment setup | <https://gaussian.com/running/> | Documents `g16 job-name`, stdin/stdout redirection, shell setup, scratch-directory behavior, and job file naming. |
| Single-point job | <https://gaussian.com/sp/> | Documents the SP job type. No-keyword HF/STO-3G behavior is a provider default, never a scientific default here. |
| Optimization and transition structures | <https://gaussian.com/opt/> | Documents Opt, Restart, TS, QST2, and QST3 behavior and prerequisites. |
| Frequency calculations | <https://gaussian.com/freq/>, <https://gaussian.com/wp-content/uploads/dl/vib.pdf> | Documents Freq/ReadFC behavior, the stationary-point requirement, and the limited meaning of negative modes. |
| Reaction paths | <https://gaussian.com/irc/> | Documents the transition-structure and force-constant prerequisites for IRC. |
| Formatted checkpoint utility | <https://gaussian.com/formchk/> | Documents `formchk [options] chkpt-file [formatted-file]`; this candidate does not run it. |
| Cube utility | <https://gaussian.com/cubegen/> | Documents the `cubegen` argument order, quantity selectors, automatic grid, and primarily atomic-unit output convention. |
| Apple platform profile | <https://gaussian.com/g16/g16_plat.pdf> | The C.02 list dated 2025-03-18 publishes Apple M-series support for macOS 12-15, shared memory, and no Linda. |
| Installation | <https://gaussian.com/g16/g16bin_install.pdf>, <https://gaussian.com/g16/g16m_install.pdf>, <https://gaussian.com/g16/g16src_install.pdf> | Public installation locators only; no installer or licensed payload is copied or run. |
| Test-job context | <https://gaussian.com/testjobs/> | Documents the provider's test-job mechanism; public test guidance is not validation of this host. |
| Commercial licensing context | <https://gaussian.com/wp-content/uploads/dl/us_com.pdf> | Public commercial material establishes a license boundary, not entitlement or redistribution permission. |

## Resolver rules

1. Match the exact requested major product and revision to a registered environment
   profile before using version-sensitive behavior.
2. Public pages may establish documented product behavior only. They cannot establish
   a local binary identity, license, successful run, or result.
3. Do not copy or redistribute licensed manuals, binaries, examples, checkpoint files,
   or user data into this repository.
4. If a decisive keyword or output convention is not established by the selected
   first-party public source and real licensed validation, mark it unresolved. Never
   fill the gap from model memory.
5. `feature-catalog.json` records the access date and stable source IDs. A URL or
   access date is still not a content hash, local installation probe, or scientific
   result.

## Known uncertainty

The public platform information and the current host profile may change. As of the
recorded 2026-07-19 review, current macOS 26.5.2 is outside the public C.02 Apple
M-series range (12-15), and no licensed binary evidence was supplied. This candidate
therefore remains offline and non-executing. Public keyword pages labeled C.01 are
used only with the separate C.02 revision-notes boundary; installed help and a real
licensed fixture are still required before promotion.
