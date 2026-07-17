# INPUT_ALL_CURRENTS — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `661298b582b8096db30f55b7c8de37189c9df04969c99a8c4f570f5bbfb57ac4`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: all_currents.x / QEHeat / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Program to compute energy current given the atomic configuration and the velocities of the atoms.

Note that a very small conv_thr must be given in the ELECTRONS namelist, in the order of 1.D-11.
The numerical derivative is very sensitive to this parameter and to "delta_t". Careful convergence
tests are needed. Note that if too relaxed values are chosen, the result can depend on the algorithm
used to diagonalize the hamiltonian a lot (the 4th/3rd digit can be wrong). Options that allows
estimating the variance are provided, to reinitialize the wavefunctions and repeat each step many
times ( "n_repeat_every_step" "re_init_wfc_1" "re_init_wfc_2" "re_init_wfc_3" ).
Performance of the calculation can be tuned a little bit with the parameters "ethr_small_step"
and "ethr_big_step", that can avoid the waste of some iterations in the diagonalization of the
hamiltonian in the first scf step of every scf calculation (the program does 2 scf for each step).
Note that in order to read atomic velocities, in the namelist CONTROL you must set calculation='md',
and in the namelist IONS you must set ion_velocities='from_input'. Algorithm for computing finite
difference derivatives can be set with the option "three_point_derivative" .

This program implements

Marcolongo, A., Umari, P. & Baroni, S.
Microscopic theory and quantum simulation of atomic heat transport.
Nature Phys 12, 80-84 (2016). https://doi.org/10.1038/nphys3509

and was originally written by Aris Marcolongo in 2014 at SISSA for his PhD thesis
( https://iris.sissa.it/handle/20.500.11767/3897 )
The all_current driver program was rewritten from scratch by Riccardo Bertossa at SISSA in 2020.
Other contributions are from Davide Tisi (SISSA), Loris Ercole (SISSA - EPFL ) and Federico Grasselli (SISSA).
Details of the implementation are discussed in
Marcolongo, Bertossa, Tisi, Baroni, https://arxiv.org/abs/2104.06383 (2021)

All the namilist but "ENERGY_CURRENT" are the same as the program pw.x

Structure of the input data:
===============================================================================

&ENERGY_CURRENT
  ...
/

&CONTROL
  MUST SET calculation='md'
  ...
/

&SYSTEM
  ...
/

&ELECTRONS
  you may want startingwfc = 'random' (for better standard deviation estimation)
  ...
/

[ &IONS
  MUST SET ion_velocities='from_input'
  ...
 / ]

[ &CELL
  ...
 / ]

ATOMIC_SPECIES
 X  Mass_X  PseudoPot_X
 Y  Mass_Y  PseudoPot_Y
 Z  Mass_Z  PseudoPot_Z

ATOMIC_POSITIONS { alat | bohr | crystal | angstrom | crystal_sg }
  X 0.0  0.0  0.0  {if_pos(1) if_pos(2) if_pos(3)}
  Y 0.5  0.0  0.0
  Z O.0  0.2  0.2

ATOMIC_VELOCITIES
  X 0.0  0.0  0.0
  Y 0.5  0.0  0.0
  Z O.0  0.2  0.2

K_POINTS { gamma }
if (gamma)
   nothing to read

[ CELL_PARAMETERS { alat | bohr | angstrom }
   v1(1) v1(2) v1(3)
   v2(1) v2(2) v2(3)
   v3(1) v3(2) v3(3) ]



========================================================================
```
