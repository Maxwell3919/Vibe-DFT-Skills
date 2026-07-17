# INPUT_PW — NAMELIST: &IONS — Variable: fnosep

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `40650beba8b329e260defd7f077a5d2b44cb5c192623661d240438a95ef02571`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       fnosep
      
      Type:           REAL
      Default:        1.D0
      Description:    oscillation frequency of the Nose thermorstat (in THz)
                      [note that 3 THz = 100 cm^-1], meaningful only with
                      "ion_temperature = 'nose'" for Nose-Hoover chain one can
                      ser frequncies for all "nhpcl" thermostats
                      ( fnosep = X Y Z etc.) If only first is set, the defaults for
                      the others will be the same.
      +--------------------------------------------------------------------
      
```
