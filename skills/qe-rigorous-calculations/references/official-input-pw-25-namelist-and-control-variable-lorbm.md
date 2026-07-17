# INPUT_PW — NAMELIST: &CONTROL — Variable: lorbm

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `af14c9225e3c76df69cd6628494584e86f94b494968a17901cd4dacefc40326a`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lorbm
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. perform orbital magnetization calculation.
                   If finite electric field is applied ("lelfield"==.true.) only Kubo terms are computed
                   [for details see New J. Phys. 12, 053032 (2010), doi:10.1088/1367-2630/12/5/053032].
                   
                   The type of calculation is 'nscf' and should be performed on an automatically
                   generated uniform grid of k points.
                   
                   Works ONLY with norm-conserving pseudopotentials.
   +--------------------------------------------------------------------
   
```
