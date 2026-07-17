# INPUT_CP — NAMELIST: &SYSTEM — Variable: exx_fraction

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `770ad23127fbdef5e1bff52d2b0b70fbf1cffc1019b3c94aaf56d7f5f5814f94`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_fraction
   
   Type:           REAL
   Default:        it depends on the specified functional
   Description:    Fraction of EXX for hybrid functional calculations. In the case of
                               input_dft='PBE0', the default value is 0.25. This entry overrides
                   the default (as well as the restart file) value of a given functional.
   +--------------------------------------------------------------------
   
```
