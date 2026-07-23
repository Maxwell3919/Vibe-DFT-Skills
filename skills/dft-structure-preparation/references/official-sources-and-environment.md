# Official sources, environment, and licenses

## Deterministic core

- Runtime: CPython 3.11 or newer using only the standard library.
- Network: not required and not used by the CLI.
- DFT engines: not required and never executed.
- Filesystem: read regular UTF-8 JSON; write only an explicitly requested new JSON file.
- Atomic file-output profile: requires POSIX-style `dir_fd` support for `open`, `stat`, `link`, and
  `unlink`; otherwise stdout remains available but file publication fails closed with
  `ATOMIC_OUTPUT_UNAVAILABLE` until a platform-equivalent no-replace adapter is validated.
- Candidate license: inherited from the repository; verify the repository license before
  redistribution.

## Provider profiles and reference-only dependencies

| Identity | Pinned distribution/version | License boundary | Activation state |
|---|---|---|---|
| `ase` | `ase==3.29.0` | LGPL-2.1-or-later; preserve notices and review optional format dependencies | metadata probe only |
| `pymatgen-wrapper` | `pymatgen==2026.5.4` | MIT; verify installed distribution metadata and notices | metadata probe only |
| `pymatgen-core` | `pymatgen-core==2026.5.18` | MIT; wrapper and core distributions retain separate identities | metadata probe only |
| spglib reference dependency | `spglib==2.7.0` | BSD-3-Clause; preserve notices and review binary packaging | unregistered review recipe only; not a provider route |
| `rdkit-pypi` | `rdkit==2026.03.4` | BSD-3-Clause; preserve notices and review bundled components | metadata probe only |

Do not interpret a package name match as API compatibility. Do not combine wrapper version and
core version into one provider identity. A version mismatch blocks integration evidence. Spglib
is not an independent identity in `registry/software-registry.yaml` or an activation requirement in
`registry/skill-registry.yaml`; use its calls only as documentation-backed review guidance. Any
future direct adapter must first add the corresponding registry identity and activation profile.

## Primary references

- ASE documentation: https://docs.ase-lib.org/
- ASE I/O: https://docs.ase-lib.org/ase/io/io.html
- ASE atoms and periodic wrapping: https://docs.ase-lib.org/ase/atoms.html
- ASE general supercells: https://docs.ase-lib.org/ase/build/tools.html
- ASE surfaces and adsorbates: https://docs.ase-lib.org/ase/build/surface.html
- pymatgen documentation: https://pymatgen.org/
- pymatgen core API: https://pymatgen.org/pymatgen.core.html
- pymatgen symmetry API: https://pymatgen.org/pymatgen.symmetry.html
- pymatgen I/O API: https://pymatgen.org/pymatgen.io.html
- pymatgen releases: https://github.com/materialsproject/pymatgen/releases/latest
- pymatgen package metadata: https://pypi.org/project/pymatgen/
- pymatgen-core project metadata: https://github.com/materialsproject/pymatgen-core/blob/main/pyproject.toml
- spglib Python interface: https://spglib.readthedocs.io/en/stable/python-interface.html
- spglib symmetry dataset: https://spglib.readthedocs.io/en/stable/dataset.html
- spglib definitions: https://spglib.readthedocs.io/en/latest/definition.html
- spglib releases: https://github.com/spglib/spglib/releases/latest
- RDKit documentation: https://www.rdkit.org/docs/
- RDKit Python guide: https://www.rdkit.org/docs/GettingStartedInPython.html
- RDKit file I/O API: https://www.rdkit.org/docs/source/rdkit.Chem.rdmolfiles.html
- RDKit molecule operations API: https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html
- RDKit conformer API: https://www.rdkit.org/docs/source/rdkit.Chem.AllChem.html
- RDKit installation guide: https://www.rdkit.org/docs/Install.html
- RDKit releases: https://github.com/rdkit/rdkit/releases/latest
- RDKit package metadata: https://pypi.org/project/rdkit/

Recheck official references against the exact provider version before integration because APIs,
defaults, binary packaging, and licensing notices are version-sensitive.

The unversioned provider pages were rechecked on 2026-07-22. Rolling documentation can be newer
than the pinned package: in particular, the pymatgen documentation header was ahead of its latest
wrapper release. Spglib 2.7.0 also changed Python exception behavior and reorganized internal
modules. Use only public top-level APIs and never treat a documentation header as installed
distribution identity.

The checked API signatures, direct temporary-directory smoke observations, and operation-specific
failure boundaries are recorded in `provider-capabilities.json`. Those checks exercised installed
ASE 3.29.0 and pymatgen-core 2026.5.18 APIs; RDKit and pymatgen-analysis-defects were absent and
were not run. This evidence is development validation, not an executable candidate route or a
scientific acceptance claim.

## Backend boundaries

pymatgen may eventually provide symmetry, standardization, slab/supercell/defect, graph, and
format adapters. ASE may eventually provide atomistic I/O, periodic wrapping, general supercells,
surfaces, adsorbates, and manual site edits. Spglib currently supplies a reference-only
symmetry cross-check, not an independent adapter or activation route. RDKit may eventually provide molecular sanitation, connectivity, stereochemistry,
conformer, and serialization adapters. Each operation requires its own task profile, parameter
record, version pin, parent route, fixtures, real artifacts, and round-trip evidence. Neither
provider may silently repair occupancy, choose charge/spin, or replace site identity.
