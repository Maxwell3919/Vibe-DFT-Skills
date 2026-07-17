# 4.2 Calculation of interatomic force constants in real space

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node9.html
- Retrieved: 2026-07-17T11:52:02+00:00
- Official source SHA-256: `a9c9900cff501a8ac9bbd76ac535b80547fb54b0a9e3c503b25b1e38c34e4b94`
- Extracted text SHA-256: `549022eafa3b569fb4f64ab56258f2a5fdb6b72662dbccde5fe7c281ddc773c8`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.3 Calculation of electron-phonon interaction

Up:

4 Using PHonon

Previous:

4.1 Single-q calculation

  

Contents

4.2 Calculation of interatomic force constants in real space

First, dynamical matrices are calculated and saved for a suitable uniform 
grid of 
q
-vectors (only those in the Irreducible Brillouin Zone of the
crystal are needed). Although this can be done one 
q
-vector at the 
time, a
simpler procedure is to specify variable 
ldisp=.true.
and to set 
variables 
nq1
, 
nq2
, 
nq3
to some suitable 
Monkhorst-Pack grid, that will be automatically generated, centered at 

$\bf q$ 
= 0. 

Second, code 
q2r.x
reads the dynamical matrices produced in the
preceding step and Fourier-transform them, writing a file of Interatomic Force
Constants in real space, up to a distance that depends on the size of the grid
of 
q
-vectors. Input documentation in the header of 
PHonon/PH/q2r.f90
.

Program 
matdyn.x
may be used to produce phonon modes and
frequencies at any 
q
using the Interatomic Force Constants file as input.
Input documentation in the header of 
PHonon/PH/matdyn.f90
.

See Example 02 for a complete calculation of phonon dispersions in AlAs.
```
