# INPUT_PW — NAMELIST: &SYSTEM — Variable: nelec_cond

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `10fc921b533a34e7b25890be62dbb14dd603a5a2e4916c1bd40d0988bfe2948d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nelec_cond
   
   Type:           REAL
   Default:        0.D0
   Description:    Number of electrons placed in the conduction manifold in a two-chemical
                   potential calculation ("twochem"=.true.). Of the total # of
                   electrons nelec, nelec-nelec_cond will occupy the valence
                   manifold and nelec_cond will be constrained in the conduction manifold.
   +--------------------------------------------------------------------
   
```
