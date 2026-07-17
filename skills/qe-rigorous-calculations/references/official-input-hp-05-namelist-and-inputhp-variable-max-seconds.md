# INPUT_HP — NAMELIST: &INPUTHP — Variable: max_seconds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `b57fd8bac796edc9e5f7518701a5209ba614303e8be4607889f995b0bc779388`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       max_seconds
   
   Type:           REAL
   Default:        1.d7
   Description:    Maximum allowed run time before the job stops smoothly.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nq1, nq2, nq3
   
   Type:           INTEGER
   Default:        1,1,1
   Description:    Parameters of the Monkhorst-Pack grid (no offset).
                   Same meaning as for nk1, nk2, nk3 in the input of pw.x.
   +--------------------------------------------------------------------
   
```
