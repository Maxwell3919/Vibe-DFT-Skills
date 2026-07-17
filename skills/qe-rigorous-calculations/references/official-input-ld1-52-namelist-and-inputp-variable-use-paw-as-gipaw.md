# INPUT_LD1 — NAMELIST: &INPUTP — Variable: use_paw_as_gipaw

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `e939f8d8c80f9421f81f575af26489ca91a97dfe13d36bd9fe9f4339637d2ac5`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       use_paw_as_gipaw
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When generating a PAW dataset, setting this option to .true. will
                   save the core all-electron wavefunctions to the UPF file.
                   The GIPAW reconstruction to be performed using the PAW data and
                   projectors for the valence wavefunctions.
                   
                   In the default case, the GIPAW valence wavefunction and projectors
                   are independent from the PAW ones and must be then specified as
                   explained above in lgipaw_reconstruction.
                   
                   Setting this to .true. always implies "lgipaw_reconstruction" = .true.
   +--------------------------------------------------------------------
   
```
