# INPUT_HP — NAMELIST: &INPUTHP — Variable: iverbosity

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `9f6dd682e029ae11d1b567af8d6d201187d7dc9f37fdcece9a98dfb58c2f9ad5`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       iverbosity
   
   Type:           INTEGER
   Default:        1
   Description:    = 1 : minimal output
                   = 2 : as above + symmetry matrices, final response
                         matrices chi0 and chi1 and their inverse matrices,
                         full U matrix
                   = 3 : as above + various detailed info about the NSCF
                         calculation at k and k+q
                   = 4 : as above + response occupation matrices at every
                         iteration and for every q point in the star
   +--------------------------------------------------------------------
   
```
