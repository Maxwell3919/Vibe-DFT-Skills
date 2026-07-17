# INPUT_LD1 — NAMELIST: &TEST — Variable: configts(i), i=1,nconf

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `d30391b5749b55b26ed6a88a5c34b8330bd1ca9fae4991371724d271d887acb4`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       configts(i), i=1,nconf
   
   Type:           CHARACTER
   Description:    A string array containing the test electronic configuration.
                   "configts"(nc), nc=1,"nconf", has the same syntax as for "config"
                   but only VALENCE states must be included.
                   If "configts"(i) is not set, the electron configuration
                   is read from the cards following the namelist.
   +--------------------------------------------------------------------
   
```
