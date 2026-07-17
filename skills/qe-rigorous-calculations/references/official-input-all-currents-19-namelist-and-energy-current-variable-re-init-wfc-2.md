# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: re_init_wfc_2

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `fb5d8e4c460f6a7a53378bf7728346d544cd96c4d7e606aecc7411f374d1cc18`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       re_init_wfc_2
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If true initializes, as specified in the ELECTRON namelist of the PW section, the wavefunctions
                   before the second ground state calculation, then compute the charge density.
                   Otherwise use the last calculated wavefunctions.
                   Note that if "three_point_derivative" is false, this has no effect.
   +--------------------------------------------------------------------
   
```
