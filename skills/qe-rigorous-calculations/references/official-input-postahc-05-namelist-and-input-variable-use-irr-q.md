# INPUT_POSTAHC — NAMELIST: &INPUT — Variable: use_irr_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_POSTAHC.txt
- Retrieved: 2026-07-17T11:49:38+00:00
- Official source SHA-256: `b0aad4211a1be89d64be4c7694d543db458ec59846a3691661e37d08bd430636`
- Extracted text SHA-256: `a36b7239735407ece98706707171e6a68859862642a4914525084a69a6291bd0`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:39 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       use_irr_q
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true., assume that the q points are on the irreducible grid. In this case,
                   the data in "ahc_dir" must have been actually generated from a calculation
                   on an irreducible q grid.
                   Off-diagonal self-energies cannot be computed if use_irr_q = .true.
   +--------------------------------------------------------------------
   
```
