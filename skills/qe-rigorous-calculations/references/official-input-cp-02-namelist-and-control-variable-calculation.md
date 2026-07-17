# INPUT_CP — NAMELIST: &CONTROL — Variable: calculation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `27c4aca731fba5575dd3ea658de79a53bfefbd88d495eb19ff1b86605a700130`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       calculation
   
   Type:           CHARACTER
   Default:        'cp'
   Description:    a string describing the task to be performed:
                      'cp',
                      'scf',
                      'nscf',
                      'relax',
                      'vc-relax',
                      'vc-cp',
                      'cp-wf',
                      'vc-cp-wf'
                   
                      (vc = variable-cell).
                      (wf = Wannier functions).
   +--------------------------------------------------------------------
   
```
