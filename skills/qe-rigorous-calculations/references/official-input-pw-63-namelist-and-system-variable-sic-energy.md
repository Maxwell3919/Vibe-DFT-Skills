# INPUT_PW — NAMELIST: &SYSTEM — Variable: sic_energy

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `b8b3b7e60b01400c6f104b9f95211b16571cb25e99f430c6a1b32140eb9c2c22`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       sic_energy
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Enable the calculation of the total energy in gammaDFT. When .true.,
                   a preliminary calculation is performed to calculate the electron density
                   in the absence of the polaron. When .false., the total energy printed in
                   output should not be considered. For structural relaxations, it is
                   recommended to use .false. to avoid doubling the computational cost.
   +--------------------------------------------------------------------
   
```
