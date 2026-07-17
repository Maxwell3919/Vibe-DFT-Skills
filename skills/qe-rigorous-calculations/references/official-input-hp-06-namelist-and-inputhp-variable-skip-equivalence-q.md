# INPUT_HP — NAMELIST: &INPUTHP — Variable: skip_equivalence_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `dd814662973da83db0c16aa96d726486d1245de2cfd98ea01e3614ef8ee40567`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       skip_equivalence_q
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. then the HP code will skip the equivalence
                   analysis of q points, and thus the full grid of q points
                   will be used. Otherwise the symmetry is used to determine
                   equivalent q points (star of q), and then perform
                   calculations only for inequivalent q points.
   +--------------------------------------------------------------------
   
```
