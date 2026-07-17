# INPUT_PW — NAMELIST: &ELECTRONS — Variable: efield_cart(i), i=1,3

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `359ef45c6f2be7a8a48237fb4c9dfb3c2bc79708e4e6e9dcd897a7573e9e6d57`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       efield_cart(i), i=1,3
   
   Type:           REAL
   Default:        (0.D0, 0.D0, 0.D0)
   Description:    Finite electric field (in Ry a.u.=36.3609*10^10 V/m) in
                   cartesian axis. Used only if "lelfield"==.TRUE. and if
                   k-points ("K_POINTS" card) are automatic.
   +--------------------------------------------------------------------
   
```
