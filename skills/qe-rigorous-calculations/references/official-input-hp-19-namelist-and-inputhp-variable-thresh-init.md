# INPUT_HP — NAMELIST: &INPUTHP — Variable: thresh_init

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `8a9a1ea1f82645c2ba40b896e58014304dfa98ef4f2c70c9e24527d3a877628a`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       thresh_init
   
   Type:           REAL
   Default:        1.D-14
   Description:    Initial threshold for the solution of the linear
                   system (first iteration). Needed to converge the
                   bare (non-interacting) response function chi0.
                   The specified value will be multiplied by the
                   number of electrons in the system.
   +--------------------------------------------------------------------
   
```
