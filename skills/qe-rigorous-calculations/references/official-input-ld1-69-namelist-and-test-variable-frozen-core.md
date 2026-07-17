# INPUT_LD1 — NAMELIST: &TEST — Variable: frozen_core

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `f82e6c10459e525e41e0d6c8ccfd804d41a2343a52ac31a27a93f4ada39ce833`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       frozen_core
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. only the core wavefunctions of the first
                   configuration are calculated. The eigenvalues, orbitals
                   and energies of the other configurations are calculated
                   with the core of the first configuration.
                   The first configuration must be spin-unpolarized.
   +--------------------------------------------------------------------
   
```
