# INPUT_PW — NAMELIST: &SYSTEM — Variable: nbnd

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `34dc96aa52468c270afceee29bb2b55921fa476f98e5147f889fa1521b55618c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nbnd
   
   Type:           INTEGER
   Default:        for an insulator, "nbnd" = number of valence bands
                   ("nbnd" = # of electrons /2);
                    for a metal, 20% more (minimum 4 more)
   Description:    Number of electronic states (bands) to be calculated.
                   Note that in spin-polarized calculations the number of
                   k-point, not the number of bands per k-point, is doubled
   +--------------------------------------------------------------------
   
```
