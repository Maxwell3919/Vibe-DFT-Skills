# INPUT_PW — NAMELIST: &SYSTEM — Variable: esm_w

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `54a5c5a9762497a31fa9d2355ea4acaeb54b5a90f9d639e7dc8c15d5d8d29bc0`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       esm_w
   
   Type:           REAL
   See:            assume_isolated
   Default:        0.d0
   Description:    If "assume_isolated" = 'esm', determines the position offset
                   [in a.u.] of the start of the effective screening region,
                   measured relative to the cell edge. (ESM region begins at
                   z = +/- [L_z/2 + esm_w] ).
   +--------------------------------------------------------------------
   
```
