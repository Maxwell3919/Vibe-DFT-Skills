# 1 Introduction

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node2.html
- Retrieved: 2026-07-17T11:50:31+00:00
- Official source SHA-256: `e9bec3ecf49c608c2e99a71e17601bfe553a3382187525214dc9b96e83b6012a`
- Extracted text SHA-256: `8c7f2dbb5158fd7c37533d387071f5e75f99061702f7fcb39d46b4c8045d3a88`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

1.1 People

Up:

User's Guide for Quantum-ESPRESSO

Previous:

Contents

  

Contents

1 Introduction

This guide gives a very general overview of
Q
UANTUM 
ESPRESSO (opEn-Source Package for Research in Electronic Structure, Simulation,
and Optimization), version 7.5.0, and explains how to build it from sources.

The Q
UANTUM 
ESPRESSO distribution contains the core packages 
PWscf
(Plane-Wave
Self-Consistent Field) and 
CP
(Car-Parrinello) for the calculation
of electronic-structure properties within
Density-Functional Theory (DFT), using a Plane-Wave (PW) basis set
and pseudopotentials. It also includes other packages for
more specialized calculations:

PWneb
:
energy barriers and reaction pathways through the Nudged Elastic Band
(NEB) method.

PHonon
:
vibrational properties with Density-Functional Perturbation Theory
(DFPT).

PostProc
:
codes and utilities for data postprocessing.

PWcond
:
ballistic conductance.

XSPECTRA
:
K-, L
1
-, L
2, 3
-edge X-ray absorption spectra.

TD-DFPT
:
spectra from Time-Dependent
Density-Functional Perturbation Theory.

GWL
: electronic excitations within the GW approximation
and with the Bethe-Salpeter Equation

EPW
: calculation of the electron-phonon coefficients,
carrier transport, phonon-limited superconductivity and phonon-assisted
optical processes;

HP
: calculation of Hubbard 
U
parameters using DFPT;

QEHeat
: energy current in insulators for thermal
transport calculations.

KCW
: quasiparticle energies of finite and extended systems
using Koopmans-compliant functionals in a Wannier representation.

The following auxiliary packages are included as well:

PWgui
:
a Graphical User Interface, producing input data files for

PWscf
and some 
PostProc
codes.

atomic
:
atomic calculations and pseudopotential generation.

Several additional packages that exploit data produced by Q
UANTUM 
ESPRESSO or patch some Q
UANTUM 
ESPRESSO routines can be downloaded and build together with Q
UANTUM 
ESPRESSO,
notably:

make
:

Wannier90
:
maximally localized Wannier functions.

WanT
:
quantum transport properties with Wannier functions.

YAMBO
:
electronic excitations within Many-Body Perturbation Theory,
GW and Bethe-Salpeter equation.

D3Q
:
anharmonic force constants.

GIPAW
(Gauge-Independent Projector Augmented Waves):
NMR chemical shifts and EPR g-tensor.

For Q
UANTUM 
ESPRESSO with the self-consistent continuum solvation (SCCS) model,
aka ``Environ'', see 
http://www.quantum-environment.org/
.

Documentation on single packages can be found in the 
Doc/

directory of each package. A detailed description of input
data is available for most packages in files 
INPUT_*.txt
and

INPUT_*.html
.

The Q
UANTUM 
ESPRESSO codes work on many different types of Unix machines,
including parallel machines using both OpenMP and MPI
(Message Passing Interface), as well as machines running
Mac OS X or MS-Windows.
Since Feb.2021 NVidia GPU's are supported by the stable releases.
AMD GPU's are also supported but not yet in the main repository
and in stable releases.

Further documentation, beyond what is provided in this guide, can be found in:

the 
Doc/
and 
examples/
directories
of the Q
UANTUM 
ESPRESSO distribution;

the web site 
www.quantum-espresso.org
;

the archives of the mailing list:
see section 
1.2
, ``Contacts'', for more info;

the Wiki pages on GitLab:

https://gitlab.com/QEF/q-e/-/wikis
.
People who want to contribute to Q
UANTUM 
ESPRESSO should read these!

This guide does not explain the basic Unix concepts (shell, execution
path, directories etc.) and utilities needed to run Q
UANTUM 
ESPRESSO; it does not
explain either solid state physics and its computational methods.
If you want to learn the latter, you should first read a good textbook,
such as e.g. the book by Richard Martin:

Electronic Structure: Basic Theory and Practical Methods
,
Cambridge University Press (2004); or:

Density functional theory: a practical introduction
,
D. S. Sholl, J. A. Steckel (Wiley, 2009); or

Electronic Structure Calculations for Solids and Molecules:
Theory and Computational Methods
,
J. Kohanoff (Cambridge University Press, 2006). Then you should consult
the documentation of the package you want to use for more specific references.

All trademarks mentioned in this guide belong to their respective owners.

Subsections

1.1 People

1.2 Contacts

1.3 Guidelines for posting to the mailing list

1.4 Terms of use

next 

up 

previous 

contents 

Next:

1.1 People

Up:

User's Guide for Quantum-ESPRESSO

Previous:

Contents

  

Contents
```
