# Official sources and version strategy

## Pinned provider

The candidate pins **CatMAP v0.4.1**, released 2024-10-08. Primary sources:

- First-party release tag: https://github.com/SUNCAT-Center/catmap/releases/tag/v0.4.1
- First-party repository and current README: https://github.com/SUNCAT-Center/catmap
- First-party GPL text: https://github.com/SUNCAT-Center/catmap/blob/v0.4.1/COPYING.txt
- First-party source documentation: https://catmap.readthedocs.io/en/latest/
- Code architecture and model components: https://catmap.readthedocs.io/en/latest/topics/code_overview.html
- ReactionModel reference and `verify()` scope: https://catmap.readthedocs.io/en/latest/reference/catmap.html
- Solver residual definition: https://catmap.readthedocs.io/en/latest/reference/catmap.solvers.html
- Thermochemistry architecture: https://catmap.readthedocs.io/en/latest/reference/catmap.thermodynamics.html
- Input/reference-energy guidance: https://catmap.readthedocs.io/en/latest/tutorials/generating_an_input_file.html
- Original method paper: A. J. Medford et al., *Catalysis Letters* 2015, 145, 794–807, https://doi.org/10.1007/s10562-015-1495-6

The v0.4.1 repository README states that the current default uses a number-of-sites-based solver and that behavior from versions at or below 0.3.2 can be requested separately. This is version-sensitive solver behavior, not a portable default.

## Documentation drift

The online documentation currently labels itself release 0.2.79 in multiple pages, while source pages can expose a different `__version__`, and the latest GitHub release is v0.4.1. Therefore:

1. the signed/tagged v0.4.1 release revision is the provider identity;
2. tag source and tag tests outrank an unversioned `latest` documentation page for implementation behavior;
3. the online documentation is used for concepts only unless a behavior is confirmed against v0.4.1 source and a forward fixture;
4. any unresolved difference produces `CAT.VERSION.SOURCE_CONFLICT` and blocks the affected task.

No behavior is inferred from `master`, an editable install, a package import alone, or a native log token.

## Version and provider policy

- Only exact v0.4.1 is accepted by this candidate.
- Earlier/later tags, forks, dirty source trees, unversioned installations, and altered solver defaults require independent profiles.
- Real execution must record source revision, tree hash, Python version, dependency lock hash, model input hashes, solver class/settings, and output hashes.
- The safe auditor never imports CatMAP. A trusted future exporter may operate only inside the pinned environment and must emit declarative JSON before this auditor runs.
- Maturity is independent for each task and mode; a steady-state tutorial does not validate sensitivity, uncertainty, electrochemistry, interactions, or multi-site behavior.

## Source-versus-science boundary

CatMAP's `verify()` checks documented model consistencies such as gas ratios, mass/site balance, prefactor format, and map resolution. Passing those checks does not prove network completeness, thermochemical correctness, solver uniqueness, physical mechanism, or predictive validity. This candidate adds evidence gates but makes no claim that they replace domain review.
