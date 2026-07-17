# INPUT_LD1 — NAMELIST: &INPUTP — Variable: pseudotype

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `5827431b28e97af5064ec8d648ba7f8d28ae3816a958fb7e61216ef9242d1a34`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pseudotype
   
   Type:           INTEGER
   Description:    1 ... norm-conserving, single-projector PP
                         IMPORTANT: if pseudotype=1 all calculations are done
                         using the SEMILOCAL form, not the separable nonlocal form
                   
                   2 ... norm-conserving PP in separable form (obsolescent)
                         All calculations are done using SEPARABLE non-local form
                         IMPORTANT: multiple projectors allowed but not properly
                         implemented, use only if you know what you are doing
                   
                   3 ... ultrasoft PP or PAW
   +--------------------------------------------------------------------
   
```
