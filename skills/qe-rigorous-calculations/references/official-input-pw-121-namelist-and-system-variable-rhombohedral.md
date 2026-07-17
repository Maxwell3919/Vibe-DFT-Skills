# INPUT_PW — NAMELIST: &SYSTEM — Variable: rhombohedral

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `292966ed538f5c2224996524bc52af8f38dc3784ee23664f637ee9880d6398e2`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       rhombohedral
   
   Type:           LOGICAL
   Default:        .TRUE.
   Description:    Used only for rhombohedral space groups.
                   When .TRUE. the coordinates of the inequivalent atoms are
                   given with respect to the rhombohedral axes, when .FALSE.
                   the coordinates of the inequivalent atoms are given with
                   respect to the hexagonal axes. They are converted internally
                   to the rhombohedral axes and "ibrav"=5 is used in both cases.
   +--------------------------------------------------------------------
   
   ///---
      VARIABLES USED ONLY IF "GATE" = .TRUE.
      
```
