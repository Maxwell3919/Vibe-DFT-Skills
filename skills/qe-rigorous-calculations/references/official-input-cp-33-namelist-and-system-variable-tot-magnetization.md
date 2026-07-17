# INPUT_CP — NAMELIST: &SYSTEM — Variable: tot_magnetization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `e37ff4234d24e2367ca70b2547f4c1035696addb1bc4be3764a7fe6940b41073`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tot_magnetization
   
   Type:           REAL
   Default:        -1 [unspecified]
   Description:    total majority spin charge - minority spin charge.
                   Used to impose a specific total electronic magnetization.
                   If unspecified, the tot_magnetization variable is ignored
                   and the electronic magnetization is determined by the
                   occupation numbers (see card OCCUPATIONS) read from input.
   +--------------------------------------------------------------------
   
```
