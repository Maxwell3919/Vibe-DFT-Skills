# INPUT_MATDYN — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `87a2c0b581cd71b5526f9d06ff1d94ea431b7003a3af8f3f8c0ccb19fe5a9dd1`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: matdyn.x / PHonon / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of matdyn.x:

This program calculates the phonon frequencies for a list of generic
q vectors starting from the interatomic force constants generated
from the dynamical matrices as written by DFPT phonon code through
the companion program q2r.x

matdyn.x can generate a supercell of the original cell for mass
approximation calculation. If supercell data are not specified
in input, the unit cell, lattice vectors, atom types and positions
are read from the force constant file.

Input data format: [ ] = it depends

Structure of the input data:
========================================================================

&INPUT
   ...specs of the namelist variables...
/

[ X(1)   Y(1)   Z(1)    ityp(1)
  ...
  X(nat) Y(nat) Z(nat)  ityp(nat) ]

[ nq
  q_x(1)  q_y(1)  q_x(1)   [ nptq(1) ]
  ...
  q_x(nq) q_y(nq) q_x(nq)  [ nptq(1) ] ]



========================================================================
```
