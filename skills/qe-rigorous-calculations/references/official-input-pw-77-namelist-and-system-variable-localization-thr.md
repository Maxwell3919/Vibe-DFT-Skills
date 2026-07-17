# INPUT_PW — NAMELIST: &SYSTEM — Variable: localization_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `2e98917ec53a103eb286e093eda6b82ff93e6077a2182fb9de9f6474bbad2c84`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       localization_thr
   
   Type:           REAL
   Default:        0.0
   Description:    Overlap threshold over which the exchange integral over a pair of localized orbitals
                   is included in the evaluation of EXX operator. Any value greater than 0.0 triggers
                   the SCDM localization and the evaluation on EXX using the localized orbitals.
                   Very small value of the threshold should yield the same result as the default EXX
                   evaluation
   +--------------------------------------------------------------------
   
```
