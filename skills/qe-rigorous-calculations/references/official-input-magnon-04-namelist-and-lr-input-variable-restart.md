# INPUT_Magnon — NAMELIST: &LR_INPUT — Variable: restart

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Magnon.txt
- Retrieved: 2026-07-17T11:49:24+00:00
- Official source SHA-256: `9d2ccecbe10a4b9f51519e86bb4361dec4c34509bf928d85f62328c09bbec0f1`
- Extracted text SHA-256: `040191a43d2e32309f15c8b93f3967b66013aa5f95972827a1a3864f696e0601`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true., turbo_magnons.x will attempt to restart
                   from a previous interrupted calculation. (see restart_step
                   variable).
                   Beware, if set to .false. turbo_magnons.x will OVERWRITE any
                   previous runs.
   +--------------------------------------------------------------------
   
```
