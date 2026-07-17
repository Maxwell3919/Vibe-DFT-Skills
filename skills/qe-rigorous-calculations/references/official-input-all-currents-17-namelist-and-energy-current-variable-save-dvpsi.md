# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: save_dvpsi

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `18548fa81aa24c0e1d625be23971c3776048d429517f16812678ceec55f03a52`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       save_dvpsi
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If true allocate the space needed for saving the solution of the linear system betweew every calculation.
                   The iterative algorithm will always start from there. By default it starts always from scratch.
   +--------------------------------------------------------------------
   
```
