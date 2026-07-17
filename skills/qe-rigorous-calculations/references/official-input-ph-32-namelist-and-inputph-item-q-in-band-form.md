# INPUT_PH — NAMELIST: &INPUTPH — Item: q_in_band_form

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `e37de454887fca4833c4d1054924980c73e12fd3efef8b36d91f54f3be29627d`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


q_in_band_form

LOGICAL

Default:

.false.

This flag is used only when qplot is .true. and q2d is
.false.. When .true. each couple of q points q(:,i+1) and
q(:,i) define the line from q(:,i) to q(:,i+1) and nq
points are generated along that line. nq is the weigth of
q(:,i). When .false. only the list of q points given as
input is calculated. The weights are not used.

[
Back to Top
]
```
