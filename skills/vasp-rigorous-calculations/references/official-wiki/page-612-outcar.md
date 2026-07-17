# OUTCAR

- Official URL: https://www.vasp.at/wiki/OUTCAR
- Page ID: 612
- Revision ID: 36630
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

There are three main output files: OUTCAR in human-readable format, vasprun.xml in xml format, and vaspout.h5 in HDF5 format. The OUTCAR file gives detailed human-readable output of a VASP run with roughly the following format:

- A summary of the used input parameters (e.g., INCAR tags), the starting structure (cf. POSCAR), the k-point mesh (cf. KPOINTS), and the pseudopotentials used (cf. POTCAR and choosing pseudopotentials).

- Information about the electronic steps, KS-eigenvalues.

- Stress tensors.

- Forces on the atoms.

- Local charges and magnetic moments.

- Dielectric properties

- The amount of output written onto the OUTCAR file can be chosen by modifying the NWRITE tag in the INCAR file.

Contents

- 1 INCAR tags

- 1.1 Common tags

- 1.2 Property tags

- 2 Related tags and articles

INCAR tags[edit | edit source]

Common tags[edit | edit source]

The output to the OUTCAR file is determined by INCAR tags. The output for these is documented on their respective tag or how-to pages. Some of the most common tags are:

- the IBRION tag selects structure optimization - IBRION = 1-3, molecular dynamics (MD) calculations - IBRION = 0, or phonon calculations - IBRION = 5-6.

- ISIF selects for degrees of ionic and structural freedom in structural optimization and MD.

- ALGO is used to define the electronic minimization algorithm that is used or to select the many-body perturbation theory (MBPT) algorithm, e.g., the GW approximation, the random-phase approximation (RPA), the Bethe-Salpeter equation (BSE).

Property tags[edit | edit source]

There are also many tags for specific properties, such as electron-phonon interactions (cf. the long list of ELPH_ tags at the end of the category page), nuclear magnetic resonance (NMR) - e.g., chemical shielding (LCHIMAG), electric field gradient EFG (LEFG), etc.

There are several other output files which we summarize below, along with several common tags for

Related tags and articles[edit | edit source]

- Output and input files: INCAR, POSCAR, KPOINTS, POTCAR, OSZICAR, IBZKPT, CHGCAR, WAVECAR, vasprun.xml, vaspout.h5.

- Controlling output verbosity: NWRITE.

- Output-controlling tags: chemical shielding, electric field gradient, hyperfine coupling constant, dielectric function, Born effective charges and dielectric tensor (DFPT), Born effective charges (finite-differences), X-ray core-level binding energies, optics, density of states (DOS).
