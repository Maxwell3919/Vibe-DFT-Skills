# INPUT_LD1 — NAMELIST: &INPUT — Variable: dx

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `5f6f9b7e2bda6ee03cf5f5a48e105d27f487568f8e740c2f5c5d430a95031852`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       dx
      
      Type:           REAL
      Description:    Radial grid parameter.
                      
                      The radial grid is: r(i+1) = exp(xmin+i*dx)/zed  a.u.
      Default:        0.0125 if "iswitch">1,
                      0.008 otherwise
      +--------------------------------------------------------------------
      
```
