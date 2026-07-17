# 1.1 What can PWscf do

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node3.html
- Retrieved: 2026-07-17T11:51:19+00:00
- Official source SHA-256: `10f656c435fb163dd536cdd84654028bb840c7de342466882e7b4b02c9e3336c`
- Extracted text SHA-256: `f0838c2a3bbc846246a25a7498e12abc1c42279d863191502ff2ba98d693f43b`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

1.2 People

Up:

1 Introduction

Previous:

1 Introduction

  

Contents

1.1 What can 
PWscf
do

PWscf
performs many different kinds of
self-consistent calculations of electronic-structure
properties within
Density-Functional Theory (DFT), using a Plane-Wave (PW) basis set and pseudopotentials (PP).
In particular:

ground-state energy and one-electron (Kohn-Sham) orbitals, 
atomic forces, stresses;

structural optimization, also with variable cell;

molecular dynamics on the Born-Oppenheimer surface, also with variable cell;

macroscopic polarization (and orbital magnetization) via 
Berry Phases;

various forms of finite electric fields, with a sawtooth potential
or with the modern theory of polarization;

Effective Screening Medium (ESM) method;

self-consistent continuum solvation (SCCS) model, if patched with
ENVIRON (
http://www.quantum-environment.org/
).

PWscf
works for both insulators and metals, 
in any crystal structure, for many exchange-correlation (XC) functionals
(including spin polarization, DFT+U, meta-GGA, nonlocal and hybrid 
functionals), for
norm-conserving (Hamann-Schluter-Chiang) PPs (NCPPs) in 
separable form or Ultrasoft (Vanderbilt) PPs (USPPs)
or Projector Augmented Waves (PAW) method.
Noncollinear magnetism and spin-orbit interactions 
are also implemented.

Please note that NEB calculations are no longer performed by 
pw.x
,
but are instead carried out by 
neb.x
(see main user guide), 
a dedicated code for path optimization which can use 
PWscf
as 
computational engine.
```
