# 3.1 Structure of the PHonon package

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node5.html
- Retrieved: 2026-07-17T11:51:57+00:00
- Official source SHA-256: `41c287ae30e194166ee3e6b1dd36b64e1a0932d1b07bae05c5314b0dcd39e278`
- Extracted text SHA-256: `55ee6626268a3029e85f820a65c04b0a721ef9e0ca692d4e8161de34bb9d2854`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.2 Compilation

Up:

3 Installation

Previous:

3 Installation

  

Contents

3.1 Structure of the 
PHonon
package

PHonon
has the following directory structure,
contained in a subdirectory 
PHonon/

of the main Q
UANTUM 
ESPRESSO tree:

Doc/

: contains the user_guide and input data description

examples/

: some running examples

PH/

: source files for phonon calculations 
and analysis

Gamma/

: source files for Gamma-only phonon calculation

FD/

: source files for FInite-Difference calculations

Important Notice:
since v.5.4, many modules and routines that were
common to all linear-response Q
UANTUM 
ESPRESSO codes are moved into the new 

LR_Modules
subdirectory of the main tree. Since v.6.0, the

D3
code for anharmonic force constant calculations has been 
superseded by the 
D3Q
code, available on

https://sourceforge.net/projects/d3q/
and automatically
downloadable from Q
UANTUM 
ESPRESSO.

The codes available in the 
PHonon
package can perform the following 
types of calculations:

phonon frequencies and eigenvectors at a generic wave vector,
using Density-Functional Perturbation Theory;

effective charges and dielectric tensors;

electron-phonon interaction coefficients for metals;

interatomic force constants in real space;

Infrared and Raman (nonresonant) cross section.

Note:
since v.5.4, packages 
PlotPhon
(for phonon
plotting) and 
QHA
(vibrational free energy in the
Quasi-Harmonic approximations), contribute by the late Prof.
Eyvaz Isaev, are no longer bundled with 
PHonon
. Their latest
version can be found in the tarballs of v.5.3 of QE.

next 

up 

previous 

contents 

Next:

3.2 Compilation

Up:

3 Installation

Previous:

3 Installation

  

Contents
```
