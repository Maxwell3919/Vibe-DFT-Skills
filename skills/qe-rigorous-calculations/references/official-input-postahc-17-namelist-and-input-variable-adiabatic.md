# INPUT_POSTAHC — NAMELIST: &INPUT — Variable: adiabatic

- Official source: https://www.quantum-espresso.org/Doc/INPUT_POSTAHC.txt
- Retrieved: 2026-07-17T11:49:38+00:00
- Official source SHA-256: `b0aad4211a1be89d64be4c7694d543db458ec59846a3691661e37d08bd430636`
- Extracted text SHA-256: `38f9fb7b7d1533142620aa2306db79a8e92a8e9ff9efd7e8d651eb7669fd1438`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:39 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       adiabatic
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true., use the adiabatic approximation when computing the Fan self-energy
                   by ignoring the phonon frequency in the denominator. This approximation is known
                   to be inaccurate and even divergent in some materials (S. Poncé et al., J. Chem.
                   Phys. 143, 102813 (2015)). Therefore, this keyword should be used only for
                   experimental or debugging purposes.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:23:33 CEST 2025
```
