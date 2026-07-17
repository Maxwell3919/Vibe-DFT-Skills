# INPUT_PW — NAMELIST: &CONTROL — Variable: lfcp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `fbaa0fff459da78aded9d7774bb3d00fa43140bafd212f0e8f0e86bce044a755`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lfcp
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. perform a constant bias potential (constant-mu) calculation
                   for a system with ESM method. See the header of PW/src/fcp_module.f90
                   for documentation. To perform the calculation, you must set a namelist FCP.
                   
                   NB:
                   - The total energy displayed in output includes the potentiostat
                     contribution (-mu*N).
                   - "calculation" must be 'relax' or 'md'.
                   - "assume_isolated" = 'esm' and "esm_bc" = 'bc2' or 'bc3' must be set
                     in "SYSTEM" namelist.
                   - ESM-RISM is also supported ("assume_isolated" = 'esm' and "esm_bc" = 'bc1'
                     and "trism" = .TRUE.).
                   - "ignore_wolfe" is always .TRUE., for BFGS.
   +--------------------------------------------------------------------
   
```
