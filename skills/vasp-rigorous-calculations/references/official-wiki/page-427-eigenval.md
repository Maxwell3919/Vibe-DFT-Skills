# EIGENVAL

- Official URL: https://www.vasp.at/wiki/EIGENVAL
- Page ID: 427
- Revision ID: 30963
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

The EIGENVAL file contains the Kohn-Sham-eigenvalues for all k-points, at the end of the simulation. For dynamic simulations (IBRION=0) the eigenvalues on the file are usually the ones predicted for the next step: i.e. the file is compatible with the CONTCAR file. For static calculations and relaxations (IBRION=-1|1|2) the eigenvalues are the solution of the KS-equations for the last step.

Mind: For dynamic simulations (IBRION=0) the EIGENVAL file contains predicted wavefunctions compatible with the CONTCAR file. If you want to use the eigenvalues for additional calculations, first copy the CONTCAR file to the POSCAR file and make another static (ISTART=1, NSW=0) continuation run with ICHARG=1.
