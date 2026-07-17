# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: warm_up_niter

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `f2aff10debffa7d2ce37d4252025b543aa286c8a03af3155d7c97efc62889ab7`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       warm_up_niter
   
   Type:           INTEGER
   Default:        0
   Description:    Runs warm_up_niter scf iterations first before applying constraint.
                   If "get_ground_state_first" is .TRUE. then scf convergence is achieved first
                   before running "warm_up_niter" scf iterations without applying the constraints.
   +--------------------------------------------------------------------
   
```
