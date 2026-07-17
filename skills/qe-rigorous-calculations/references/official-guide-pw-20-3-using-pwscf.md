# 3 Using PWscf

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node7.html
- Retrieved: 2026-07-17T11:51:24+00:00
- Official source SHA-256: `9c241bed336bd98c19347b0f5a385e3ef3cf8c5123520f50a8d4963887bbfa3e`
- Extracted text SHA-256: `6baf91214efdf86fe64f016ad6157231775dd474c9dca08de9008286dab01c73`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.1 Input data

Up:

User's Guide for the PWscf

Previous:

2 Compilation

  

Contents

3 Using 
PWscf

Input files for 
pw.x
may be either written by hand 
or produced via the 
PWgui
graphical interface by Anton Kokalj, 
included in the Q
UANTUM 
ESPRESSO distribution. See 
PWgui-x.y.z/INSTALL

(where x.y.z is the version number) for more info on 
PWgui
, 
or 
GUI/README
if you are using sources from the repository.

You may take the tests (in 
test-suite/
) and examples
(in 
PW/examples/
) distributed with Q
UANTUM 
ESPRESSO as templates for
writing your own input files. You may find input files (typically
with names ending with 
.in
) either in 
test-suite/pw_*/

or in the various 
PW/examples/*/results/
subdirectories,
after you have run the examples. All examples contain a README file.

Subsections

3.1 Input data

3.2 Data files

3.3 Electronic structure calculations

3.3.0.1 Single-point (fixed-ion) SCF calculation

3.3.0.2 Band structure calculation

3.3.0.3 Noncollinear magnetization, spin-orbit interactions

3.3.0.4 DFT+U

3.3.0.5 Dispersion Interactions (DFT-D)

3.3.0.6 Hartree-Fock and Hybrid functionals

3.3.0.7 Dispersion interaction with non-local functional (vdW-DF)

3.3.0.8 Polarization via Berry Phase

3.3.0.9 Finite electric fields

3.3.0.10 Orbital magnetization

3.4 Optimization and dynamics

3.4.0.1 Structural optimization

3.4.0.2 Molecular Dynamics

3.4.0.3 Variable-cell optimization

3.4.0.4 Variable-cell molecular dynamics

3.5 Direct interface with 
CASINO

3.5.0.1 Practicalities

3.5.0.2 How to generate 
xwfn.data
files with 
PWscf

3.6 Socket interface with i-PI

3.6.0.1 Practicalities

3.6.0.2 How to use the i-PI inteface

3.6.0.3 Advanced i-PI usage
```
