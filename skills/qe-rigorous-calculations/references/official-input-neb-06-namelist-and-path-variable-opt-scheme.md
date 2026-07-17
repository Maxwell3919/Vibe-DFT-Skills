# INPUT_NEB — NAMELIST: &PATH — Variable: opt_scheme

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `f40a731ad91c253c77f6c23fce97db534f2b3c4564ba091cdcc685afafe3ccd2`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       opt_scheme
         
         Type:           CHARACTER
         Default:        'quick-min'
         Description:   
                         Specify the type of optimization scheme:
          
                         'sd' :
                              steepest descent
          
                         'broyden' :
                              quasi-Newton Broyden's second method (suggested)
          
                         'broyden2' :
                              another variant of the quasi-Newton Broyden's
                              second method to be tested and compared with the
                              previous one.
          
                         'quick-min' :
                              an optimisation algorithm based on the
                              projected velocity Verlet scheme
          
                         'langevin' :
                              finite temperature langevin dynamics of the
                              string (smd only). It is used to compute the
                              average path and the free-energy profile.
         +--------------------------------------------------------------------
         
```
