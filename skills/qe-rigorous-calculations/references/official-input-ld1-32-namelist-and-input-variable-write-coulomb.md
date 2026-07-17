# INPUT_LD1 — NAMELIST: &INPUT — Variable: write_coulomb

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `0eed5ce3e1f595ff5caafe746a43b5de61dfedb1e647d0a6490cbf735213b022`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       write_coulomb
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true., a fake pseudo-potential file with name X.UPF,
                   where X is the atomic symbol, is written. It contains
                   the radial grid and the wavefunctions as specified in input,
                   plus the info needed to build the Coulomb potential
                   for an all-electron calculation - for testing only.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
