# INPUT_PW — NAMELIST: &SYSTEM — Variable: starting_spin_angle

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `591c22b740b1be3f7d84c8cda8d2b21c5cf1d76e95218192d6c4d8965194a6bf`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       starting_spin_angle
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    In the spin-orbit case when "domag"=.TRUE., by default,
                   the starting wavefunctions are initialized as in scalar
                   relativistic noncollinear case without spin-orbit.
                   
                   By setting "starting_spin_angle"=.TRUE. this behaviour can
                   be changed and the initial wavefunctions are radial
                   functions multiplied by spin-angle functions.
                   
                   When "domag"=.FALSE. the initial wavefunctions are always
                   radial functions multiplied by spin-angle functions
                   independently from this flag.
                   
                   When "lspinorb" is .FALSE. this flag is not used.
   +--------------------------------------------------------------------
   
```
