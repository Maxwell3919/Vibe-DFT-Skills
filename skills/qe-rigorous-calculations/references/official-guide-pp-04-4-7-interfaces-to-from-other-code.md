# 4.7 Interfaces to/from other code

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node12.html
- Retrieved: 2026-07-17T11:52:12+00:00
- Official source SHA-256: `cae492d85255c3bece2fa9d330b59d27283636cc903ef6aac05402a2aff68195`
- Extracted text SHA-256: `5d76aec3b2862862cb10f9d098da39bbc19ecbb2aa9dec5be5c7807873396c83`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.8 Other tools

Up:

4 Usage

Previous:

4.6 Wannier functions

  

Contents

4.7 Interfaces to/from other code

Codes 
pw2bgw.x
convert data files from 
pw.x
to a format suitable
for usage by the Berkeley GW code. See file 
Doc/INPUT_pw2bgw.*

for input data documentation. Code 
bgw2pw.x
, performing the
inverse conversion, no longer works: a copy that worked for the old
file format is kept for reference in 
bgw2pw.f90.orig
.

Code 
pw2gw.x
converts data files from 
pw.x
to a format suitable 
for usage by another GW code, computes optical properties in single-particle 
approach (Fermi Golden Rule). See file 
Doc/INPUT_pw2gw.html

for input data documentation, directory 
pw2gw_example/

for an example of usage.

Code 
open_grid.x
writes Kohn-Sham orbitals for the complete
k-point grid (not symmetry-independent points only) in real space.
Useful for further processing. It can be used to generate the
Kohn-Sham state data required in 
pw2wannier.x
and Wannier90
from the initial SCF calculation, bypassing the non-SCF calculation
step.

Code 
pw2critic.x
is an interface to the CRITIC2 code by
Alberto Otero-de-la-Roza. This program creates a 
pwc
file
containing the Kohn-Sham orbitals from an SCF calculation (or from the
output of 
open_grid.x
). These orbitals are used for
post-processing in CRITIC2.

Code 
pw_export.f90
no longer works and is no longer present.
```
