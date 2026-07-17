# pw_user_guide.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `98b7cb723d696c14dc17b21f0f990cdce180604e12e1a6e43b22d2afbb8c34e9`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
1     Introduction
This guide covers the usage of the PWscf (Plane-Wave Self-Consistent Field) package, a core
component of the Quantum ESPRESSO distribution. Further documentation, beyond what
is provided in this guide, can be found in the directory PW/Doc/, containing a copy of this guide
(note: all directories are relative to the root directory of Quantum ESPRESSO).
    This guide assumes that you know the physics that PWscf describes and the methods it
implements. It also assumes that you have already installed, or know how to install, Quantum
ESPRESSO. If not, please read the general User’s Guide in directory Doc/; or consult the
web site: http://www.quantum-espresso.org.
    People who want to modify or contribute to PWscf should read the Wiki pages on GitLab:
https://gitlab.com/QEF/q-e/-/wikis.

1.1    What can PWscf do
PWscf performs many different kinds of self-consistent calculations of electronic-structure prop-
erties within Density-Functional Theory (DFT), using a Plane-Wave (PW) basis set and pseu-
dopotentials (PP). In particular:

     ground-state energy and one-electron (Kohn-Sham) orbitals, atomic forces, stresses;

     structural optimization, also with variable cell;

     molecular dynamics on the Born-Oppenheimer surface, also with variable cell;

     macroscopic polarization (and orbital magnetization) via Berry Phases;

     various forms of finite electric fields, with a sawtooth potential or with the modern theory
      of polarization;

     Effective Screening Medium (ESM) method;

     self-consistent continuum solvation (SCCS) model, if patched with ENVIRON (http://www.quant

PWscf works for both insulators and metals, in any crystal structure, for many exchange-
correlation (XC) functionals (including spin polarization, DFT+U, meta-GGA, nonlocal and
hybrid functionals), for norm-conserving (Hamann-Schluter-Chiang) PPs (NCPPs) in separable
form or Ultrasoft (Vanderbilt) PPs (USPPs) or Projector Augmented Waves (PAW) method.
Noncollinear magnetism and spin-orbit interactions are also implemented.
   Please note that NEB calculations are no longer performed by pw.x, but are instead carried
out by neb.x (see main user guide), a dedicated code for path optimization which can use
PWscf as computational engine.

1.2    People
The PWscf package (which in earlier releases included PHonon and PostProc) was originally
developed by Stefano Baroni, Stefano de Gironcoli, Andrea Dal Corso (SISSA), Paolo Giannozzi
(Univ. Udine), and many others. We quote in particular:

     David Vanderbilt’s group at Rutgers for Berry’s phase calculations;


                                                2
```
