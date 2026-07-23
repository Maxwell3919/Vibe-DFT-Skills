# Environment, license, and external-tool boundary

## Repository runtime

The catalog and deterministic guard require Python 3.10 or newer and the
standard library only. They read bounded local JSON/text evidence and never
import, launch, download, or install Multiwfn. `multiwfn_catalog.py probe`
resolves executable names and Python distribution metadata only; it does not
run a banner or help command.

On 2026-07-22 the checked Darwin arm64 host had no `Multiwfn` or `multiwfn` in
`PATH` and no Python distribution named `multiwfn`. No native menu or example
was run, so the exact state is `native-not-run` rather than unsupported,
passing, or scientifically validated.

## Official distributions and platform boundary

The official download page publishes Windows and Linux packages. It provides a
full Linux distribution and a noGUI distribution. The full build can require
graphical libraries, including Motif as documented by the official manual. The
noGUI build avoids the graph dependency but omits graph-related functionality;
it cannot be substituted for GUI topology, DOS, spectrum, or visualization
steps.

The official page does not provide an official macOS release. It links the
independent community repository
`https://github.com/digital-chemistry-laboratory/multiwfn-mac-build` and warns
that the available build may not match the current version. The community
repository likewise states that it is independent and provides no guarantee.
Keep that route blocked until its exact source revision/build provenance,
banner/update date, package and executable digests, architecture, settings,
and exact-menu regression evidence are reviewed. A link from the official page
does not turn the community binary into an official distribution.

## Runtime configuration

Before a future execution adapter is enabled, record:

- official distribution URL, package digest, executable digest, platform, and
  architecture;
- full/noGUI identity and the exact program banner/update date;
- `settings.ini` path and SHA-256 and any `Multiwfnpath` configuration;
- physical-core/thread choice and the effective thread count;
- required graphical/shared libraries;
- `OMP_STACKSIZE`, process stack (`ulimit`), and shared-memory settings when the
  selected workload needs them;
- input/stdin/output hashes and a complete private stdout/stderr transcript;
- each external converter, viewer, Gaussian call, or other auxiliary program as
  a separately authorized/versioned adapter.

The official manual warns that command-line arguments may not take effect when
`settings.ini` cannot be found. Treat that condition as a configuration
failure. Do not infer that `-nt`, `-set`, `-silent`, or another argument was
honored from the command text alone.

Run fixed-output workflows only in a new scratch directory. Do not overwrite
`ELF.cub`, `bndmat.txt`, `sl2r.cub`, `dg_inter.cub`, `hole.cub`,
`electron.cub`, or any task-dependent output. A stale file is not execution
evidence.

## License, citation, privacy, and external tools

The official download page is the authority for current license and citation
obligations. On the 2026-07-22 review, it described Multiwfn as free and
open-source for academic and commercial use, allowed redistribution of original
or modified code under its stated conditions, required prior Tian Lu consent
before selling a modified version, and disclaimed warranty. This is a concise
technical routing note, not legal advice; review the live page for every
execution or redistribution campaign and do not cache acceptance for a user.

The same live page required both general citations in the main text when
Multiwfn or its code is used:

1. T. Lu and F. Chen, *J. Comput. Chem.* **33**, 580-592 (2012),
   `https://doi.org/10.1002/jcc.22885`.
2. T. Lu, *J. Chem. Phys.* **161**, 082503 (2024),
   `https://doi.org/10.1063/5.0216272`.

Some functions have additional recommended citations. Consult the official
`How to cite Multiwfn` document or the corresponding manual section for the
specific analysis; the two general papers are not a complete
function-specific bibliography.

Wavefunction files and analysis outputs may contain unpublished structures and
results. Keep raw inputs, absolute paths, account names, private binaries, and
real numerical artifacts outside this repository. Commit only synthetic
fixtures and safe hashes/labels.
