# 4.8 Fourier interpolation of phonon potential

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node15.html
- Retrieved: 2026-07-17T11:51:41+00:00
- Official source SHA-256: `f2ba1206fb3230edf80f1ef13a6025df14550dab25fed1871d961f0990b5b3c9`
- Extracted text SHA-256: `c9cdcf744241ef33418907d8357cb7b7dd36722c6aa43fe39872cb99f9e7d8ea`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.9 Calculation of phonon-renormalization of

Up:

4 Using PHonon

Previous:

4.7 Phonons from DFPT+U

  

Contents

4.8 Fourier interpolation of phonon potential

The potential perturbation caused by the displacement of a single atom is
spatially localized. Hence, the phonon potential can be interpolated from

q
points on a coarse grid to other 
q
points using Fourier interpolation.
To use this functionality, first, one shoud run a 
ph.x
calculation for 
q

points on a regular coarse grid.
Then, a 
dvscf_q2r.x
run performs an inverse Fourier
transformation of the phonon potentials from a 
q
grid to a real-space
supercell. Finally, by specifying 
ldvscf_interpolation=.true.
in

ph.x
, the phonon potentials are Fourier transformed to given 
q
points.

For insulators, the nonanalytic long-ranged dipole part of the potential needs
to be subtracted and added before and after the interpolation, respectively.
This treatment is activated by specifying 
do_long_range=.true.
in the
input files of 
dvscf_q2r.x
and 
ph.x
.

Due to numerical inaccuracies, the calculated Born effective charges may not
add up to zero, violating the charge neutrality condition. This error may lead
to nonphysical polar divergence of the phonon potential for 
q
points close
to 
Γ
, even in IR-inactive materials. To avoid this problem, one can
specify 
do_charge_neutral=.true.
in the input files of

dvscf_q2r.x
and 
ph.x
. Then, the phonon potentials and the Born
effective charges are renormalized by enforcing the charge neutrality condition,
following the scheme of S.  Ponce et al, J. Chem. Phys. (2015).

The Fourier interpolation of phonon potential is proposed and described in the
following papers:

A. Eiguren and C. Ambrosch-Draxl, Phys. Rev. B 
78
, 045124 (2008);

S.  Ponce et al, J. Chem. Phys. 
143
, 102813 (2015);

X. Gonze et al, Comput. Phys. Commun., 
248
, 107042 (2020).

next 

up 

previous 

contents 

Next:

4.9 Calculation of phonon-renormalization of

Up:

4 Using PHonon

Previous:

4.7 Phonons from DFPT+U

  

Contents
```
