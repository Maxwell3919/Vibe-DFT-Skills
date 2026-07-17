# LCHARG

- Official URL: https://www.vasp.at/wiki/LCHARG
- Page ID: 90
- Revision ID: 37108
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LCHARG = [logical]
Default: LCHARG = .True.

Description: Determines whether the charge density is written.

For LCHARG = T (default), the files CHGCAR and CHG are written.
If LH5 = T , the charge density is instead written to vaspwave.h5.

Mind: For VASP version 6.0 to 6.4.2 the default for LCHARG = .NOT.LH5

Related tags and articles[edit | edit source]

Restart and output files cheat sheet

LWAVE, LCHARGH5, LH5, LTAU

Workflows that use this tag
