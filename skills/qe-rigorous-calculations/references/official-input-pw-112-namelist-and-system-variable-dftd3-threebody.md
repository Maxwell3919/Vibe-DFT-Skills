# INPUT_PW — NAMELIST: &SYSTEM — Variable: dftd3_threebody

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `fbd97912b4f07c595a2753f72b0f0511a51821de55ecb7417821e5ad4ff416f3`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dftd3_threebody
   
   Type:           LOGICAL
   Default:        TRUE
   Description:    Turn three-body terms in Grimme-D3 on. If .false. two-body contributions
                   only are computed, using two-body parameters of Grimme-D3.
                   If dftd3_version=2, three-body contribution is always disabled.
   +--------------------------------------------------------------------
   
```
