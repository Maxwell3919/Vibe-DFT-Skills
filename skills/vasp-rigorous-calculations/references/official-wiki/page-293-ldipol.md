# LDIPOL

- Official URL: https://www.vasp.at/wiki/LDIPOL
- Page ID: 293
- Revision ID: 34205
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LDIPOL = .TRUE. | .FALSE.
Default: LDIPOL = .FALSE.

Description: LDIPOL switches on corrections to the potential and forces. Can be applied for charged molecules and slabs with a net dipole moment.

The presence of a dipole in combination with periodic boundary conditions leads to a slow convergence of the total energy with the size of the supercell.
Furthermore, finite-size errors affect the potential and the forces.
This effect can be counterbalanced by setting LDIPOL=.TRUE. in the INCAR file.
For LDIPOL=.TRUE., a linear correction, and for charged cells, a quadratic electrostatic potential is added to the local potential in order to correct the errors introduced by the periodic boundary conditions. When activating this tag the tag IDIPOL has to be specified, and optionally the tag DIPOL as well.

Mind: This is in the spirit of Neugebauer et al. [1], though more general. Note that the total energy is correctly implemented, whereas Ref. [1] contains an erroneous factor 2 in the total energy.

The biggest advantage of this mode is that leading errors in the forces are corrected and that the work function can be evaluated for asymmetric slabs. The disadvantage is that the convergence to the electronic ground state might slow down considerably, i.e., more electronic iterations might be required to obtain the required precision.

Important: Dipole corrections can lead to slow convergence, since charge often needs to be moved from one side of a slab to the other. The convergence rate often improves by setting AMIN to a smaller value, for instance AMIN = 0.01, since this dampens charge sloshing (charge moving back and forth from one to the other side of the slab in consecutive steps). Sometimes, it might also be necessary to increase the number of electronic steps using NELM and to tighten the energy convergence EDIFF = 1E-6. An unconverged dipole correction can lead to erroneous forces [[1]].

Warning: For charged systems, the potential correction is currently only implemented for cubic supercells. VASP will stop if the supercell is not cubic and LDIPOL is used.

Related tags and articles[edit | edit source]

Monopole Dipole and Quadrupole corrections,
NELECT,
EPSILON,
IDIPOL,
DIPOL,
LMONO,
EFIELD

Examples that use this tag

References[edit | edit source]

- ↑ a b J. Neugebauer and M. Scheffler, Phys. Rev. B 46, 16067 (1992).
