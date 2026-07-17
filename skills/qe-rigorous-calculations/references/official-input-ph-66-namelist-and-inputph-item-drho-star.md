# INPUT_PH — NAMELIST: &INPUTPH — Item: drho_star

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `4e866600a6d999592520d7f8f1140cffb18dcfcd10174862a8c7d7cb97ad8a44`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


drho_star

STRUCTURE

Default:

disabled

See:

dvscf_star

It contains the following components:

drho_star%open
(logical, default: .false.)

drho_star%dir
(character, default: outdir//"Rotated_DRHO" or the
ESPRESSO_FILDRHO_DIR environment variable)

drho_star%ext
(character, default: "drho") the extension to use
for the name of the output files, see below

drho_star%basis
(character, default: "modes") the basis on which
the rotated drho will be saved

drho_star%pat
(logical, default: true) save an optional file with the
displacement patterns and q vector for each drho file

Like 
dvscf_star
, but for the perturbation of the charge density.
Notice that the defaults are different.

[
Back to Top
]

IF 
ldisp != .true. and qplot != .true.
:
```
