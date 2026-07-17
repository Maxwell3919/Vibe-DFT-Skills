# INPUT_PW — NAMELIST: &SYSTEM — Variable: report

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `85ed743af3c65126b710afeff575ce9b1d22c3aedc5cd18da043748ceb769336`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       report
   
   Type:           INTEGER
   Default:        -1
   Description:    determines when atomic magnetic moments are printed on output:
                   report = 0  never
                   report =-1  at the beginning of the scf and at convergence
                           report = N  as -1, plus every N scf iterations
   +--------------------------------------------------------------------
   
```
