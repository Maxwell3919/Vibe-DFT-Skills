# 4 Using PHonon

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node7.html
- Retrieved: 2026-07-17T11:52:00+00:00
- Official source SHA-256: `1ffd4519685dcb5d33defac9821044e7adb56ab1ca732c56c6cf464387511f51`
- Extracted text SHA-256: `9397f05506841428ca620d63dda5c4ed2dcea0577dcf52441c9f56c1eeda7249`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.1 Single-q calculation

Up:

User's Guide for the PHonon

Previous:

3.2 Compilation

  

Contents

4 Using 
PHonon

Phonon calculation is presently a two-step process.
First, you have to find the ground-state atomic and electronic configuration;
Second, you can calculate phonons using Density-Functional Perturbation Theory.
Further processing to calculate Interatomic Force Constants, to add macroscopic
electric field and impose Acoustic Sum Rules at 
$\bf q$ 
= 0 may be needed.
In the following, we will indicate by 
$\bf q$ 
the phonon wavevectors, 
while 
$\bf k$ 
will indicate Bloch vectors used for summing over the 
Brillouin Zone.

The main code 
ph.x
can be used whenever 
PWscf
can be used, with the
exceptions of hybrid and meta-GGA functionals, external electric fields,
constraints on magnetization, nonperiodic boundary conditions.
USPP and PAW are not implemented for higher-order response calculations.
See the header of file 
PHonon/PH/phonon.f90
for a complete and
updated list of what 
PHonon
can and cannot do.

Since version 4.0 it is possible to safely stop execution of 
ph.x
code using
the same mechanism of the 
pw.x
code, i.e. by creating a file 

prefix.EXIT
in the working directory. Execution can be resumed by 
setting 
recover=.true.
in the subsequent input data.
Moreover the execution can be (cleanly) stopped after a given time is elapsed,
using variable 
max_seconds
. See 
example/Recover_example/
.

Subsections

4.1 Single-
q
calculation

4.2 Calculation of interatomic force constants in real space

4.3 Calculation of electron-phonon interaction coefficients

4.4 DFPT with the tetrahedron method

4.5 Calculation of electron-phonon interaction coefficients with the tetrahedron method

4.6 Phonons for two-dimensional crystals

4.7 Phonons from DFPT+
U

4.8 Fourier interpolation of phonon potential

4.9 Calculation of phonon-renormalization of electron bands
```
