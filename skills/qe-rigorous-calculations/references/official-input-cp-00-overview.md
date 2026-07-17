# INPUT_CP — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `4795b727365fbcca516b47a72ad112142b77946e17d22ad9fdf40008ad4be852`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: cp.x / CP / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, | = or

All quantities whose dimensions are not explicitly specified are in
HARTREE ATOMIC UNITS. Charge is "number" charge (i.e. not multiplied
by e); potentials are in energy units (i.e. they are multiplied by e)

BEWARE: TABS, CRLF, ANY OTHER STRANGE CHARACTER, ARE A SOURCES OF TROUBLE
USE ONLY PLAIN ASCII TEXT FILES (CHECK THE FILE TYPE WITH UNIX COMMAND "file")

Namelists must appear in the order given below.
Comment lines in namelists can be introduced by a "!", exactly as in
fortran code. Comments lines in ``cards'' can be introduced by
either a "!" or a "#" character in the first position of a line.
Do not start any line in ``cards'' with a "/" character.
Leave a space between card names and card options, e.g.
ATOMIC_POSITIONS (bohr), not ATOMIC_POSITIONS(bohr)

Structure of the input data:
===============================================================================

&CONTROL
  ...
/

&SYSTEM
 ...
/

&ELECTRONS
...
/

[ &IONS
  ...
 / ]

[ &CELL
  ...
 / ]

[ &WANNIER
  ...
 / ]

ATOMIC_SPECIES
 X  Mass_X  PseudoPot_X
 Y  Mass_Y  PseudoPot_Y
 Z  Mass_Z  PseudoPot_Z

ATOMIC_POSITIONS { alat | bohr | crystal | angstrom }
  X 0.0  0.0  0.0  {if_pos(1) if_pos(2) if_pos(3)}
  Y 0.5  0.0  0.0
  Z O.0  0.2  0.2

[ CELL_PARAMETERS { alat | bohr | angstrom }
   v1(1) v1(2) v1(3)
   v2(1) v2(2) v2(3)
   v3(1) v3(2) v3(3) ]

[ OCCUPATIONS
   f_inp1(1)  f_inp1(2)  f_inp1(3) ... f_inp1(10)
   f_inp1(11) f_inp1(12) ... f_inp1(nbnd)
 [ f_inp2(1)  f_inp2(2)  f_inp2(3) ... f_inp2(10)
   f_inp2(11) f_inp2(12) ... f_inp2(nbnd) ] ]

[ CONSTRAINTS
   nconstr  { constr_tol }
   constr_type(.)   constr(1,.)   constr(2,.) [ constr(3,.)   constr(4,.) ] { constr_target(.) } ]

[ ATOMIC_FORCES
   label_1 Fx(1) Fy(1) Fz(1)
   .....
   label_n Fx(n) Fy(n) Fz(n) ]



========================================================================
```
