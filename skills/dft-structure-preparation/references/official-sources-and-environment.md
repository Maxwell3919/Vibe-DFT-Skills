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

## Optional provider profiles

| Provider profile | Pinned distribution/version | License boundary | Activation state |
|---|---|---|---|
| `ase` | `ase==3.29.0` | LGPL-2.1-or-later; preserve notices and review optional format dependencies | metadata probe only |
| `pymatgen-wrapper` | `pymatgen==2026.5.4` | MIT; verify installed distribution metadata and notices | metadata probe only |
| `pymatgen-core` | `pymatgen-core==2026.5.18` | MIT; wrapper and core distributions retain separate identities | metadata probe only |
| `rdkit-pypi` | `rdkit==2026.03.4` | BSD-3-Clause; preserve notices and review bundled components | metadata probe only |

Do not interpret a package name match as API compatibility. Do not combine wrapper version and
core version into one provider identity. A version mismatch blocks integration evidence.

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

The checked API signatures, direct temporary-directory smoke observations, and operation-specific
failure boundaries are recorded in `provider-capabilities.json`. Those checks exercised installed
ASE 3.29.0 and pymatgen-core 2026.5.18 APIs; RDKit and pymatgen-analysis-defects were absent and
were not run. This evidence is development validation, not an executable candidate route or a
scientific acceptance claim.

## Backend boundaries

pymatgen may eventually provide symmetry, standardization, slab/supercell/defect, graph, and
format adapters. ASE may eventually provide atomistic I/O, periodic wrapping, general supercells,
surfaces, adsorbates, and manual site edits. RDKit may eventually provide molecular sanitation, connectivity, stereochemistry,
conformer, and serialization adapters. Each operation requires its own task profile, parameter
record, version pin, parent route, fixtures, real artifacts, and round-trip evidence. Neither
provider may silently repair occupancy, choose charge/spin, or replace site identity.
