# INPUT_PW — NAMELIST: &SYSTEM — Variable: Hubbard_beta(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `0a6c7d7f935282ba9331b703d6f6469aadd070e09220494c177835b3020f0171`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       Hubbard_beta(i), i=1,ntyp
   
   Type:           REAL
   Default:        0.D0 for all species
   Description:    Hubbard_beta(i) is the perturbation (on atom i, in eV)
                   used to compute J0 with the linear-response method of
                   Cococcioni and de Gironcoli, PRB 71, 035105 (2005)
                   (only for DFT+U or DFT+U+V). See also
                   PRB 84, 115108 (2011).
   +--------------------------------------------------------------------
   
```
