# INPUT_PW — NAMELIST: &RISM — Variable: laue_expand_right

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `8ef8db6b63dda44d3496a2e1962dddb0bfcddf7a6847571e39755e2fd5c169bd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_expand_right
   
   Type:           REAL
   Default:        -1.0
   Description:    If positive value, set the ending position offset [in a.u.]
                   of the solvent region on right-hand side of the unit cell,
                   measured relative to the unit cell edge.
                   (the solvent region ends at z = + [L_z/2 + "laue_expand_right"].)
                   This is only for Laue-RISM.
   +--------------------------------------------------------------------
   
```
