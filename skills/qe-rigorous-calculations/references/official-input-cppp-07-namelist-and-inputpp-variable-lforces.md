# INPUT_CPPP — NAMELIST: &INPUTPP — Variable: lforces

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CPPP.txt
- Retrieved: 2026-07-17T11:49:00+00:00
- Official source SHA-256: `9a1344351309e168957be343641bf7f2ffe66f2c597f8b5a14d2617f2f3e2d6b`
- Extracted text SHA-256: `c77935171c778bd47a7d3f7457848b1671d5e4815852ccf6165fcb00c8a1647d`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lforces
   
   Type:           LOGICAL
   Default:        .false.
   Description:    This logical flag control the processing of forces.
                   
                       .TRUE.  extract forces from trajectory files and write
                               them to xcrysden file
                   
                       .FALSE. do not process forces
   +--------------------------------------------------------------------
   
```
