# INPUT_LD1 — NAMELIST: &INPUTP — Variable: file_pseudopw

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `82f7d3b1847cb3cde70b09d6cb3cfcba7bb432950b816a7229ae1395a33d17df`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       file_pseudopw
   
   Type:           CHARACTER
   Status:         REQUIRED
   Description:    File where the generated PP is written.
                   
                   * if the file name ends with "upf" or "UPF",
                   or in any case for spin-orbit PP (rel=2),
                   the file is written in UPF format;
                   
                   * if the file name ends with 'psp' it is
                   written in native CPMD format (this is currently
                   an experimental feature); otherwise it is written
                   in the old "NC" format if pseudotype=1, or
                   in the old RRKJ format if pseudotype=2 or 3
                   (no default, must be specified).
   +--------------------------------------------------------------------
   
```
