# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: pawproj

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `94e6bcb5cbb2b8579b73ca22350f00e32b34bd254435f5a7798a732a20058868`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pawproj
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true. use PAW projectors and all-electron PAW basis
                   functions to calculate weight factors for the partial
                   densities of states. Following Bloechl, PRB 50, 17953 (1994),
                   Eq. (4 & 6), the weight factors thus approximate the real
                   charge within the augmentation sphere of each atom.
                   Only for PAW, not implemented in the noncolinear case.
   +--------------------------------------------------------------------
   
```
