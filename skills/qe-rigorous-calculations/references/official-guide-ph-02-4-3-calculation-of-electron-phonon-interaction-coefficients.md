# 4.3 Calculation of electron-phonon interaction coefficients

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node10.html
- Retrieved: 2026-07-17T11:51:34+00:00
- Official source SHA-256: `ce5826479e9239cc6e208dba6ffc7053dbe13565e894fe5ac07e3c2d71b48aaf`
- Extracted text SHA-256: `768beb54a26ada6c7ba11f18f02881fe78a575cafb66922fa0975c40ff431580`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.4 DFPT with the tetrahedron

Up:

4 Using PHonon

Previous:

4.2 Calculation of interatomic force

  

Contents

4.3 Calculation of electron-phonon interaction coefficients

Since v.5.0, there are two ways of calculating electron-phonon
coefficients, distinguished according to the value of variable 

electron_phonon
. The following holds for the case 

electron_phonon=

'interpolated'
(see also Example 03).

The calculation of electron-phonon coefficients in metals is made difficult 
by the slow convergence of the sum at the Fermi energy. It is convenient to 
use a coarse 
k
-point grid to calculate phonons on a suitable 
wavevector grid;
a dense 
k
-point grid to calculate the sum at the Fermi energy. 
The calculation
proceeds in this way:

a scf calculation for the dense 
$\bf k$ 
-point grid (or a scf calculation 
followed by a non-scf one on the dense 
$\bf k$ 
-point grid); specify 
option 
la2f=.true.
to 
pw.x
in order to save a file with 
the eigenvalues on the dense 
k
-point grid. The latter MUST contain 
all 
$\bf k$ 
and 

$\bf k$ 
+ 
$\bf q$ 
grid points used in the subsequent 
electron-phonon 
calculation. All grids MUST be unshifted, i.e. include 
$\bf k$ 
= 0.

a normal scf + phonon dispersion calculation on the coarse 
k
-point
grid, specifying option 
electron_phonon='interpolated'
, and 
the file name where
the self-consistent first-order variation of the potential is to be 
stored: variable 
fildvscf
).
The electron-phonon coefficients are calculated using several
values of Gaussian broadening (see 
PHonon/PH/elphon.f90
) 
because this quickly
shows whether results are converged or not with respect to the 

k
-point grid and Gaussian broadening.

Finally, you can use 
matdyn.x
and 
lambda.x

(input documentation in the header of 
PHonon/PH/lambda.f90
)
to get the 

α
2
F
(
ω
) function, the electron-phonon coefficient

λ
, and an estimate of the critical temperature 
T
c
.

See the appendix for the relevant formulae.

Important notice
: the 

q
→ 0 limit of the contribution 
to the electron-phonon coefficient diverges for optical modes! please 
be very careful, consult the relevant literature.

next 

up 

previous 

contents 

Next:

4.4 DFPT with the tetrahedron

Up:

4 Using PHonon

Previous:

4.2 Calculation of interatomic force

  

Contents
```
