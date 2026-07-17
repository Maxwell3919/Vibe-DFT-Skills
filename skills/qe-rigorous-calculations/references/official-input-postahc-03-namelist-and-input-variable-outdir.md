# INPUT_POSTAHC — NAMELIST: &INPUT — Variable: outdir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_POSTAHC.txt
- Retrieved: 2026-07-17T11:49:38+00:00
- Official source SHA-256: `b0aad4211a1be89d64be4c7694d543db458ec59846a3691661e37d08bd430636`
- Extracted text SHA-256: `a6e7556c67cdbad6ff830bcc121a72bd3e42f65e407fe27cc289bd6169242906`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:39 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       outdir
   
   Type:           CHARACTER
   Default:        value of the ESPRESSO_TMPDIR environment variable if set;
                    current directory ('./') otherwise
   Description:    Directory containing input, output, and scratch files;
                   must be the same as specified in the calculation of
                   the unperturbed system.
   +--------------------------------------------------------------------
   
```
