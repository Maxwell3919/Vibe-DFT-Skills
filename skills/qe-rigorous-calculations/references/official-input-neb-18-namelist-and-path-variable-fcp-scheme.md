# INPUT_NEB — NAMELIST: &PATH — Variable: fcp_scheme

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `15b088c310e3911810496e22f5eac7f420ba91a65f807222682439a5adb18a81`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       fcp_scheme
         
         Type:           CHARACTER
         See:            lfcp
         Default:        'lm'
         Description:   
                         Specify the type of optimization scheme for FCP:
          
                         'lm' :
                              Line-Minimization method.
          
                         'newton' :
                              Newton-Raphson method with diagonal hessian matrix.
                              Also, coupling with DIIS.
          
                         'coupled' :
                              Coupled method with ionic positions.
                              This is available only if "opt_scheme" == 'broyden',
                              or 'broyden2'.
         +--------------------------------------------------------------------
         
      ===END OF NAMELIST======================================================
      
      
      ========================================================================
```
