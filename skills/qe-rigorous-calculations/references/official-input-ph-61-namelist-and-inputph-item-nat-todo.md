# INPUT_PH — NAMELIST: &INPUTPH — Item: nat_todo

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `7ec6f38b17161b91ca2d6a71ef06a96a33c54d9d20b5b1d9f2a06c856cdc00a6`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


nat_todo

INTEGER

Default:

0, i.e. displace all atoms

Choose the subset of atoms to be used in the linear response
calculation: 
nat_todo
atoms, specified in input (see below)
are displaced. Can be used to estimate modes for a molecule
adsorbed over a surface without performing a full fledged
calculation. Use with care, at your own risk, and be aware
that this is an approximation and may not work.
IMPORTANT:
* 
nat_todo
<= nat
* if linear-response is calculated for a given atom, it
should also be done for all symmetry-equivalent atoms,
or else you will get incorrect results

[
Back to Top
]
```
