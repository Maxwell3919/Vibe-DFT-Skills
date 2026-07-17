# INPUT_PW — NAMELIST: &SYSTEM — Variable: lgcscf

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `7982dfae37056691f8667c05e8d6fafe2f46e57063dd991497d7364218f0af67`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lgcscf
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. perform a constant bias potential (constant-mu) calculation
                   with Grand-Canonical SCF. (JCP 146, 114104 (2017), R.Sundararaman, et al.)
                   
                   NB:
                   - The total energy displayed in output includes the potentiostat
                     contribution (-mu*N).
                   - "assume_isolated" = 'esm' and "esm_bc" = 'bc2' or 'bc3' must be set
                     in "SYSTEM" namelist.
                   - ESM-RISM is also supported ("assume_isolated" = 'esm' and "esm_bc" = 'bc1'
                     and "trism" = .TRUE.).
                   - "mixing_mode" has to be 'TF' or 'local-TF', also its default is 'TF.'
                   - The default of "mixing_beta" is 0.1 with ESM-RISM, 0.2 without ESM-RISM.
                   - The default of "diago_thr_init" is 1.D-5.
                   - "diago_full_acc" is always .TRUE. .
                   - "diago_rmm_conv" is always .TRUE. .
   +--------------------------------------------------------------------
   
```
