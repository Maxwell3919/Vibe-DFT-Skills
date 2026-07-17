# INPUT_PH — NAMELIST: &INPUTPH — Item: diagonalization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `4549404f0c0717443d99ea89e454812490ef5aa186891e3a3d5f4e6450bf4793`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


diagonalization

CHARACTER

Default:

'david'

Diagonalization method for the non-SCF calculations.

'david'
:

Davidson iterative diagonalization with overlap matrix
(default). Fast, may in some rare cases fail.

'cg'
:

Conjugate-gradient-like band-by-band diagonalization.
Slower than 'david' but uses less memory and is
(a little bit) more robust.

[
Back to Top
]
```
