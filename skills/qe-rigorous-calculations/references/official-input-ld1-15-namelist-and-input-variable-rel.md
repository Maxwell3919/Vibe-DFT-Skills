# INPUT_LD1 — NAMELIST: &INPUT — Variable: rel

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `8f2fc45b5cb678d34ad65d133371805242d7f1c381ac34a225507d76d7359c72`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       rel
   
   Type:           INTEGER
   Description:    0 ... non relativistic calculation
                   1 ... scalar relativistic calculation
                   2 ... full relativistic calculation with spin-orbit
   Default:        0 for Z <= 18;
                   1 for Z >  18
   +--------------------------------------------------------------------
   
```
