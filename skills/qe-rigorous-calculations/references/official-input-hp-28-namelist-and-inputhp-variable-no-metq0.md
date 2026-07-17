# INPUT_HP — NAMELIST: &INPUTHP — Variable: no_metq0

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `a1886a53edfc9ea2126b52c428f70d7b62e60817553363e8f530211251bef3cd`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       no_metq0
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. the metallic response term at q=0 is ignored
                   (i.e. the last term in Eq. (22) in PRB 103, 045141 (2021)).
                   This is useful for magnetic insulators to avoid the divergence
                   of the calculation.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:25:41 CEST 2025
```
