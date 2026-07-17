# INPUT_PH — NAMELIST: &INPUTPH — Item: dvscf_star

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `1737d29c93dd1da413159bbb70a6ddeff18c5602730d79a3239528026ea96d06`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


dvscf_star

STRUCTURE

Default:

disabled

It contains the following components:

dvscf_star%open
(logical, default: .false.)

dvscf_star%dir
(character, default: outdir//"Rotated_DVSCF" or the
ESPRESSO_FILDVSCF_DIR environment variable)

dvscf_star%ext
(character, default: "dvscf") the extension to use
for the name of the output files, see below

dvscf_star%basis
(character, default: "cartesian") the basis on which
the rotated dvscf will be saved

dvscf_star%pat
(logical, default: false) save an optional file with the
displacement patterns and q vector for each dvscf file

IF dvscf_star%open is .true. use symmetry to compute and store the variation
of the self-consistent potential on every q* in the star of the present q.

The rotated dvscf will then be stored in directory dvscf_star%dir with name
prefix.dvscf_star%ext.q_name//"1". Where q_name is derived from the coordinates
of the q-point, expressed as fractions in crystalline coordinates
(notice that ph.x reads q-points in cartesian coordinates).
E.g. q_cryst= (0, 0.5, -0.25) -> q_name = "0_1o2_-1o4"

The dvscf can be represented on a basis of cartesian 1-atom displacements
(dvscf_star%basis='cartesian') or on the basis of the modes at the rotated q-point
(dvscf_star%basis='modes'). Notice that the el-ph wannier code requires 'cartesian'.
Each dvscf file comes with a corresponding pattern file with an additional ".pat"
suffix; this file contains information about the basis and the q-point of the dvscf.

Note: rotating dvscf can require a large amount of RAM memory and can be i/o
intensive; in its current implementation all the operations are done
on a single processor.
Note2: this feature is currently untested with image parallelisation.

[
Back to Top
]
```
