# ISMEAR

- Official URL: https://www.vasp.at/wiki/ISMEAR
- Page ID: 183
- Revision ID: 37501
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

ISMEAR = -15 | -14 | -5 | -4 | -3 | -2 | -1 | 0 | [integer]>0
Default: ISMEAR = 1

Description: ISMEAR determines how the partial occupancies fnk are set for each orbital. SIGMA determines the width of the smearing in eV.

Please consider how-to guide to choose the optimal smearing technique.

Tag options[edit | edit source]

- ISMEAR > 0: method of Methfessel-Paxton order ISMEAR with width SIGMA.

Mind: Methfessel-Paxton can yield erroneous results for insulators because the partial occupancies can be unphysical.

- ISMEAR = 0: Gaussian smearing with width SIGMA.

- ISMEAR = -1: Fermi smearing with width SIGMA.

- ISMEAR = -2: Partial occupancies are read in from the WAVECAR and kept fixed throughout run. Alternatively, you can also choose occupancies in the INCAR file with the tag FERWE (and FERDO for ISPIN = 2 calculations).

- ISMEAR = -3: perform a loop over SMEARINGS parameters supplied in the INCAR file.

- ISMEAR = -4: Tetrahedron method without smearing.

- ISMEAR = -5: Tetrahedron method with Blöchl corrections[1] without smearing.

- ISMEAR = -14: Tetrahedron method with Fermi-Dirac smearing SIGMA.

- ISMEAR = -15: Tetrahedron method with Blöchl corrections[1] with Fermi-Dirac smearing SIGMA.

Mind: Use a Γ-centered k-mesh for the tetrahedron methods.

Related tags and articles[edit | edit source]

SIGMA,
EFERMI,
FERWE,
FERDO,
SMEARINGS,
Smearing technique,
K-point integration

Examples that use this tag

References[edit | edit source]

- ↑ a b P.E. Blöchl, O. Jepsen, and O.K. Andersen, Phys. Rev. B 49, 16223 (1994).
