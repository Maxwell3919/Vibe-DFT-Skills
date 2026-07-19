# Environment, license, and external calculators

The deterministic guard requires Python 3.10 or newer and the standard library only. It does not import or execute Phonopy.

For future real execution, create a clean environment with the exact Phonopy distribution and dependency lock. Version 4.3.1 documentation records the v4 CLI split (`phonopy-init` for setup/collection and `phonopy` for calculations) and recent Rust-backend behavior. The pinned package manifest requires Python 3.10 or newer, NumPy, PyYAML, Matplotlib, h5py, spglib, symfc, and phonors. `seekpath`, `pypolymlp>=0.10.0`, and `cp2k-input-tools` are route-specific optional dependencies. The install page also lists SciPy even though the pinned core manifest does not; inspect the actual installed metadata.

Record Python, Phonopy, NumPy, PyYAML, h5py, Matplotlib, spglib, symfc, phonors, calculator interface, optional extras, package hashes, executable paths, platform, architecture, and backend banner. The pinned console parsers do not define `--version`; use `python -c 'import phonopy; print(phonopy.__version__)'` and each relevant entrypoint's `-h`. Do not confuse `phonopy -v` (verbose) with a version probe. Do not silently use `phonopy-load` or a pre-v4 command sequence.

The official conda route is `conda install -c conda-forge phonopy`; this document describes it but does not authorize automatic installation. On NFS, `HDF5_USE_FILE_LOCKING=FALSE` is an official targeted workaround for HDF5 locking problems, not a global default.

Phonopy delegates forces or force constants to external calculators. The v4.3.1 parser lists ABACUS, ABINIT, FHI-aims, CASTEP, CP2K, CRYSTAL, DFTB+, Elk, Fleur, LAMMPS, PWmat, Questaal, QE, SIESTA, TURBOMOLE, VASP, and WIEN2k selectors. Route QE, VASP, CP2K, or SIESTA calculations through their calculation Skills and apply equivalent official-parent validation for every other calculator. A Phonopy-readable file is not proof that the parent calculation completed or converged.

The official source repository license text is the authority for Phonopy redistribution. Each force calculator, pseudopotential/potential dataset, and optional library has separate terms. Never commit restricted potentials, real calculation trees, private paths, or unpublished forces. Synthetic fixtures in this candidate are not reference data.
