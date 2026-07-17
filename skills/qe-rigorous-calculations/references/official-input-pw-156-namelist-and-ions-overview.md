# INPUT_PW — NAMELIST: &IONS — overview

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `5c282734bf4ea3db570c13199ead67ed7eabf566f957a752e0c0dab6aa83f86f`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
NAMELIST: &IONS

   REQUIRED IF "CALCULATION" == 'RELAX', 'MD', 'VC-HRELAX', OR 'VC-MD'
   OPTIONAL FOR "CALCULATION" == 'SCF' (ONLY "ION_POSITIONS" IS USED)
   
```
