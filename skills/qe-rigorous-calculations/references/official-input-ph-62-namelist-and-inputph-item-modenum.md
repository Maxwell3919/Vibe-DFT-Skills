# INPUT_PH — NAMELIST: &INPUTPH — Item: modenum

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `7b7d7afa08155961834891526f7139c42ef1944214fe73efa433eb82ad1c7030`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


modenum

INTEGER

Default:

0

For single-mode phonon calculation : modenum is the index of the
irreducible representation (irrep) into which the reducible
representation formed by the 3*nat atomic displacements are
decomposed in order to perform the phonon calculation.
Note that a single-mode calculation will not give you the
frequency of a single phonon mode: in general, the selected
"modenum" is not an eigenvector. What you get on output is
a column of the dynamical matrix.

[
Back to Top
]

q-point specification
```
