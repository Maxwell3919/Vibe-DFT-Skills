# INPUT_LD1 — NAMELIST: &INPUTP — Variable: zval

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `2ea46f1881066d29bff91fa8072eb82c93b55ebb46f25be2da3d1691fbfbf681`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       zval
   
   Type:           REAL
   Default:        (calculated)
   Description:    Valence charge.
                   
                   zval is automatically calculated from available data.
                   If the value of zval is provided in input, it will be
                   checked versus the calculated value. The only case in
                   which you need to explicitly provide the value of zval
                   for noninteger zval (i.e. half core-hole pseudo-potentials).
   +--------------------------------------------------------------------
   
```
