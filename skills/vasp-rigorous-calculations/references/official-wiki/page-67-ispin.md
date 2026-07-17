# ISPIN

- Official URL: https://www.vasp.at/wiki/ISPIN
- Page ID: 67
- Revision ID: 36282
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

ISPIN = 1 | 2
Default: ISPIN = 1

Description: ISPIN specifies whether a calculation is performed with or without spin polarization.

In spin-polarized calculations, VASP treats spin-up and spin-down electrons separately, allowing each spin channel to develop a different charge density and occupation. This is essential for magnetic systems; for nonmagnetic systems it is generally unnecessary and increases computational cost.

- ISPIN=1: VASP performs a non-spin-polarized calculation. Spin-up and spin-down electrons share a single charge density.

- ISPIN=2: VASP performs a spin-polarized collinear calculation. Spin-up and spin-down electrons are treated separately.

Spin-polarized calculations are commonly used for magnetic materials such as Fe, Co, Ni, and magnetic oxides. To initialize magnetic moments on atoms, combine ISPIN=2 with MAGMOM.

ISPIN = 2
MAGMOM = 2*5.0 2*-5.0

This example initializes two atoms with positive magnetic moments and two atoms with negative magnetic moments, which may be useful for antiferromagnetic calculations.

Mind: For noncollinear calculations, ISPIN is ignored; use LNONCOLLINEAR=.TRUE. instead.

Mind: Since VASP 6.5.0, the calculation exits with an error if ISPIN=2 and MAGMOM are used together with LNONCOLLINEAR=.TRUE.

Related tags and articles[edit | edit source]

MAGMOM
LNONCOLLINEAR

Examples that use this tag
