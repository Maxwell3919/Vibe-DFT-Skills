# 3.2 Compilation

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node6.html
- Retrieved: 2026-07-17T11:51:58+00:00
- Official source SHA-256: `b2f4580fe6a7277fa705b4800a7c1f77fa762442189c0c031d0f4b5290270675`
- Extracted text SHA-256: `abca6acbd599b69ac0182873acfc323e210ca6e4c8002508537154e39056607d`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4 Using PHonon

Up:

3 Installation

Previous:

3.1 Structure of the PHonon

  

Contents

3.2 Compilation

Typing 
make ph
from the root Q
UANTUM 
ESPRESSO directory, or 
make

from the 
PHonon
directory, produces the following codes:

PH/ph.x
: Calculates phonon frequencies and displacement patterns,
dielectric tensors, effective charges (uses data produced by 
pw.x
). 

PH/dynmat.x
: applies various kinds of Acoustic Sum Rule (ASR),
calculates LO-TO splitting at 

$\bf q$ 
= 0 in insulators, IR and Raman
cross sections (if the coefficients have been properly calculated),
from the dynamical matrix produced by 
ph.x

PH/q2r.x
: calculates Interatomic Force Constants (IFC) in real space
from dynamical matrices produced by 
ph.x
on a regular 
q
-grid 

PH/matdyn.x
: produces phonon frequencies at a generic wave vector
using the IFC file calculated by 
q2r.x
; may also calculate phonon
DOS, the electron-phonon coefficient 
λ
, the function

α
2
F
(
ω
)

PH/lambda.x
: also calculates 
λ
and 

α
2
F
(
ω
),
plus 
T
c
for superconductivity using the McMillan formula

PH/alpha2f.x
: also calculates 
λ
and 

α
2
F
(
ω
).
It is used together with the optimized tetrahedron method and shifted

q
-grid

PH/fqha.x
: a simple code to calculate vibrational entropy with
the quasi-harmonic approximation

PH/dvscf_q2r.x
: performs inverse Fourier transformation of phonon
potential from a regular 
q
grid to real space.

Gamma/phcg.x
:
a version of 
ph.x
that calculates phonons at 

$\bf q$ 
= 0 using
conjugate-gradient minimization of the density functional expanded to
second-order. Only the 
Γ
(

$\bf k$ 
= 0) point is used for
Brillouin zone integration. It is faster and takes less memory than

ph.x
, but does not support spin polarization, USPP and PAW.

Links to the main Q
UANTUM 
ESPRESSO 
bin/
directory are automatically generated.

next 

up 

previous 

contents 

Next:

4 Using PHonon

Up:

3 Installation

Previous:

3.1 Structure of the PHonon

  

Contents
```
