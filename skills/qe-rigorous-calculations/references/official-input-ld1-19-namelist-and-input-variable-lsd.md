# INPUT_LD1 — NAMELIST: &INPUT — Variable: lsd

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `35ae50d3e7f035d3ad821d4a700f628b2c064ab980546c20b8e9d867a1ad7bb2`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lsd
   
   Type:           INTEGER
   Description:    0 ... non spin polarized calculation
                   1 ... spin-polarized calculation
                   
                   BEWARE:
                   not allowed if "iswitch"=3 (PP generation) or with full
                   relativistic calculation
   Default:        0
   +--------------------------------------------------------------------
   
```
