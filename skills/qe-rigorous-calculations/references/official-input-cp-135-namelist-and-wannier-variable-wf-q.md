# INPUT_CP — NAMELIST: &WANNIER — Variable: wf_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `9c9739c7ebea2794a07f3da79653edfd120187caa8c7d9f9d1a4fb9a85a3d9f9`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wf_q
   
   Type:           REAL
   Default:        1500.D0
   Description:    Fictitious mass of the A matrix used for obtaining
                   maximally localized Wannier functions. The unitary
                   transformation matrix U is written as exp(A) where
                   A is a anti-hermitian matrix. The Damped-Dynamics is performed
                   in terms of the A matrix, and then U is computed from A.
                   Usually a value between 1500 and 2500 works fine, but should
                   be tested.
   +--------------------------------------------------------------------
   
```
