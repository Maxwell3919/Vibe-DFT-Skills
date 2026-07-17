# INPUT_CPPP — NAMELIST: &INPUTPP — Variable: lrotation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CPPP.txt
- Retrieved: 2026-07-17T11:49:00+00:00
- Official source SHA-256: `9a1344351309e168957be343641bf7f2ffe66f2c597f8b5a14d2617f2f3e2d6b`
- Extracted text SHA-256: `c65fbc2d07678303047da2ee0088d2b6ea457c3fc8caa5f7d75c888878bbf4ea`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lrotation
   
   Type:           LOGICAL
   Default:        .false.
   Description:    This logical flag control the rotation of the cell
                   
                       .TRUE.  rotate the system cell in space in order to have
                               the a lattice parameter laying on the x axis,
                               the b lattice parameter laying on the xy plane
                   
                       .FALSE. do not rotate cell
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      np1, np2, np3
   
   Type:           INTEGER
   Default:        1
   Description:    Number of replicas of atomic positions along cell parameters.
                   CURRENTLY DISABLED
                   
                   If np1, np2, np3 are 1 or not specified, cppp.x does not
                   replicate atomic positions in space.
                   
                   If np1, np2, np3 are > 1 cppp.x replicates the atomic
                   positions used in the simulation np1 times along "a",
                   np2 times along "b", np3 times along "c".
   +--------------------------------------------------------------------
   
```
