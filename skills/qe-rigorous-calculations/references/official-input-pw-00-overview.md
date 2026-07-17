# INPUT_PW — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `0db0b9f7de6023b9dc303ab7a1faa18dd234dedda568394b7935c49e6b6b323d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: pw.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, | = or

All quantities whose dimensions are not explicitly specified are in
RYDBERG ATOMIC UNITS. Charge is "number" charge (i.e. not multiplied
by e); potentials are in energy units (i.e. they are multiplied by e).

BEWARE: TABS, CRLF, ANY OTHER STRANGE CHARACTER, ARE A SOURCES OF TROUBLE
USE ONLY PLAIN ASCII TEXT FILES (CHECK THE FILE TYPE WITH UNIX COMMAND "file")

Namelists must appear in the order given below.
Comment lines in namelists can be introduced by a "!", exactly as in
fortran code. Comments lines in cards can be introduced by
either a "!" or a "#" character in the first position of a line.
Do not start any line in cards with a "/" character.
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

[ &FCP
  ...
 / ]

[ &RISM
  ...
 / ]

ATOMIC_SPECIES
 X  Mass_X  PseudoPot_X
 Y  Mass_Y  PseudoPot_Y
 Z  Mass_Z  PseudoPot_Z

ATOMIC_POSITIONS { alat | bohr | angstrom | crystal | crystal_sg }
  X 0.0  0.0  0.0  {if_pos(1) if_pos(2) if_pos(3)}
  Y 0.5  0.0  0.0
  Z 0.0  0.2  0.2

K_POINTS { tpiba | automatic | crystal | gamma | tpiba_b | crystal_b | tpiba_c | crystal_c }
if (gamma)
   nothing to read
if (automatic)
   nk1, nk2, nk3, k1, k2, k3
if (not automatic)
   nks
   xk_x, xk_y, xk_z,  wk
if (tpipa_b or crystal_b in a 'bands' calculation) see Doc/brillouin_zones.pdf

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

[ ATOMIC_VELOCITIES
   label(1)  vx(1) vy(1) vz(1)
   .....
   label(n)  vx(n) vy(n) vz(n) ]

[ ATOMIC_FORCES
   label(1)  Fx(1) Fy(1) Fz(1)
   .....
   label(n)  Fx(n) Fy(n) Fz(n) ]

[ ADDITIONAL_K_POINTS
     see: K_POINTS ]

[ SOLVENTS
   label(1)     Density(1)     Molecule(1)
   label(2)     Density(2)     Molecule(2)
   .....
   label(nsolv) Density(nsolv) Molecule(nsolv) ]

[ HUBBARD { atomic | ortho-atomic | norm-atomic | wf | pseudo }
  if (DFT+U)
      U     label(1)-manifold(1) u_val(1)
    [ J0    label(1)-manifold(1) j0_val(1) ]
    [ ALPHA label(1)-manifold(1) alpha_val(1) ]
      .....
      U     label(n)-manifold(n) u_val(n)
    [ J0    label(n)-manifold(n) j0_val(n) ]
    [ ALPHA label(n)-manifold(n) alpha_val(n) ]
  if (DFT+U+J)
      paramType(1) label(1)-manifold(1) paramValue(1)
      .....
      paramType(n) label(n)-manifold(n) paramValue(n)
  if (DFT+U+V)
      U  label(I)-manifold(I) u_val(I)
    [ J0 label(I)-manifold(I) j0_val(I) ]
      V  label(I)-manifold(I) label(J)-manifold(J) I J v_val(I,J)
      .....
      U  label(N)-manifold(N) u_val(N)
    [ J0 label(N)-manifold(N) j0_val(N) ]
      V  label(N)-manifold(N) label(M)-manifold(M) N M v_val(N,M)
  if (DFT+U (orbital-resolved))
      U     label(1)-shell(1) u_val(1)      eigenstate(1) [... eigenstate(4l+2)]
    [ ALPHA label(1)-shell(1) alpha_val(1)  eigenstate(1) [... eigenstate(4l+2)]  ]
      .....
      U     label(n)-shell(n) u_val(n)      eigenstate(n) [... eigenstate(4l+2)]
    [ ALPHA label(n)-shell(n) alpha_val(n)  eigenstate(n) [... eigenstate(4l+2)]  ]
All Hubbard parameters must be specified in eV.
manifold  = 3d, 2p, 4f...
shell  = 3d, 2p, 4f...
paramType = U, J, B, E2, or E3
eigenstate = 1, 2, 3, ..., 10 (d-shell)
Check Doc/Hubbard_input.pdf for more details. ]



========================================================================
```
