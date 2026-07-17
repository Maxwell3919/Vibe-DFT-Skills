# INPUT_NEB — NAMELIST: &PATH — Variable: lfcp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `1b7f3ae00ee0f04ea73cb3ea9884dc00bc0690d137cfe8fcd764314e8341176e`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       lfcp
         
         Type:           LOGICAL
         See:            fcp_mu
         Default:        .FALSE.
         Description:    If .TRUE. perform a constant bias potential (constant-mu) calculation with
                         - ESM method (assume_isolated = 'esm' and esm_bc = 'bc2' or 'bc3' must be
                                       set in SYSTEM namelist) or
                         - ESM-RISM method (assume_isolated = 'esm' and esm_bc = 'bc1' must be set
                                            set in SYSTEM namelist, and trism = .TRUE. must be set
                                            set in CONTROL namelist).
                         
                         "fcp_mu" gives the target Fermi energy.
                         See the header of PW/src/fcp_module.f90 for documentation
         +--------------------------------------------------------------------
         
```
