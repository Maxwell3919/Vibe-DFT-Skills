# INPUT_PH — NAMELIST: &INPUTPH — Item: lmultipole

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `f4162c44f132ae102bb7e43e6038b983323e37af7f9009ee5ac90cad7e016d6d`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


lmultipole

LOGICAL

Default:

.false.

If .true. prints the induced density and potentials in fildrho and fildvscf.
To extract multipoles and the finite-q dielectric function, multiple finite-q
calculations need to be performed (see test-suite/ph_multipole,
where multipole.py manages the flow of the calculations as described in test-suite/run-ph.sh).
N.B.: works only for 3d systems.

[
Back to Top
]

Optional variables for Raman:
```
