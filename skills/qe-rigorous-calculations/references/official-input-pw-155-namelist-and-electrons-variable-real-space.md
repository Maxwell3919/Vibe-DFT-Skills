# INPUT_PW — NAMELIST: &ELECTRONS — Variable: real_space

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e05dba93df3fb4c3e81e9e3820d8f64bdf161a2e15f3996d0c37d6e603789539`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       real_space
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .true., exploit real-space localization to compute
                   matrix elements for nonlocal projectors. Faster and in
                   principle better scaling than the default G-space algorithm,
                   but numerically less accurate, may lead to some loss of
                   translational invariance. Use with care and after testing!
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
