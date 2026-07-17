# LDAUPRINT

- Official URL: https://www.vasp.at/wiki/LDAUPRINT
- Page ID: 152
- Revision ID: 36502
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LDAUPRINT = 0 | 1
Default: LDAUPRINT = 0

Description: LDAUPRINT controls the verbosity of a DFT+U calculation.

- LDAUPRINT=0: No onsite occupancy matrix is written to the OUTCAR file.

- LDAUPRINT=1: The spin up and spin down onsite occupancy matrices of the atoms types to which a [math]\displaystyle{ U }[/math] is applied are written to the OUTCAR file at each iteration (below "onsite density matrix"). The eigenvalues and eigenvectors of the total (spin up + spin down) onsite matrix is also written (below "occupancies and eigenvectors").

Related tags and articles[edit | edit source]

LDAU,
LDAUTYPE,
LDAUL,
LDAUU,
LDAUJ,
LMAXMIX

Examples that use this tag
