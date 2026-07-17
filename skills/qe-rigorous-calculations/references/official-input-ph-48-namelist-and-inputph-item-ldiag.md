# INPUT_PH — NAMELIST: &INPUTPH — Item: ldiag

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `005bfa2b38be734a84ae96abfb2e2bb6a5ce3bdc1c63e7e7f376f43e3c4f5be0`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


ldiag

LOGICAL

Default:

.false.

If .true. forces the diagonalization of the dynamical
matrix also when only a part of the dynamical matrix
has been calculated. It is used together with 
start_irr

and 
last_irr
. If all modes corresponding to a
given irreducible representation have been calculated,
the phonon frequencies of that representation are
correct. The others are zero or wrong. Use with care.

[
Back to Top
]
```
