# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: re_init_wfc_1

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `e86d246062d9627811602231a6db21e7e44d60ef26f7a859b94954878596f3c8`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       re_init_wfc_1
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If true initializes, as specified in the ELECTRON namelist of the PW section, the wavefunctions
                   before the first ground state calculation, then compute the charge density.
                    Otherwise use the last calculated wavefunctions.
   +--------------------------------------------------------------------
   
```
