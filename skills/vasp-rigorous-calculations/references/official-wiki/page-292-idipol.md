# IDIPOL

- Official URL: https://www.vasp.at/wiki/IDIPOL
- Page ID: 292
- Revision ID: 28126
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

IDIPOL = 1 | 2 | 3 | 4

Description: IDIPOL switches on monopole/dipole and quadrupole corrections to the total energy in a specific direction (1-3) or all directions (4)

IDIPOL = 1-3[edit | edit source]

The dipole moment will be calculated only parallel to the direction of the first, second or third lattice vector, respectively. The corrections for the total energy are calculated as the energy difference between a monopole/dipole and quadrupole in the current supercell and the same dipole placed in a super cell with the corresponding lattice vector approaching infinity.

Tip: This flag should be used for slab calculations, with the surface normal being the direction in which the IDIPOL is set, and optionally specifying the center of mass of the slab with the DIPOL tag.

IDIPOL = 4[edit | edit source]

For IDIPOL=4 the full dipole moment in all directions will be calculated, and the corrections to the total energy are calculated as the energy difference between a monopole/dipole/quadrupole in the current supercell and the same monopole/dipole/quadrupole placed in a vacuum.

Tip: Use this flag for calculations for isolated molecules.

Note: strictly speaking quadrupole corrections is not the proper wording. The relevant quantity is

[math]\displaystyle{ \int d^3{\mathbf r} \rho(\mathbf r) \Vert \mathbf r\Vert^2. }[/math]

Related tags and articles[edit | edit source]

Monopole Dipole and Quadrupole corrections,
NELECT,
EPSILON,
DIPOL,
LDIPOL,
LMONO,
EFIELD

Examples that use this tag
