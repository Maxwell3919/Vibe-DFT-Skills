# INPUT_PW — NAMELIST: &ELECTRONS — Variable: tqr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e1ba3f8515bdd5643f13c5bafd5011983af325176b314f5d8c145b5d902dcf01`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tqr
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .true., use a real-space algorithm for augmentation
                   charges of ultrasoft pseudopotentials and PAWsets.
                   Faster but numerically less accurate than the default
                   G-space algorithm. Use with care and after testing!
   +--------------------------------------------------------------------
   
```
