# INPUT_HP — NAMELIST: &INPUTHP — Variable: outdir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `a6e7556c67cdbad6ff830bcc121a72bd3e42f65e407fe27cc289bd6169242906`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
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
