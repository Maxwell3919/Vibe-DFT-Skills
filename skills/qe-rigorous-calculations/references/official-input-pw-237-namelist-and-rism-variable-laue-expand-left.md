# INPUT_PW — NAMELIST: &RISM — Variable: laue_expand_left

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `3f6f03a00262a8f51840c3602e0c07d1d9cd79f11ed61743288cd86337fc9b09`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_expand_left
   
   Type:           REAL
   Default:        -1.0
   Description:    If positive value, set the ending position offset [in a.u.]
                   of the solvent region on left-hand side of the unit cell,
                   measured relative to the unit cell edge.
                   (the solvent region ends at z = - [L_z/2 + "laue_expand_left"].)
                   This is only for Laue-RISM.
   +--------------------------------------------------------------------
   
```
