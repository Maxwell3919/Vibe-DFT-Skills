# INPUT_PW — NAMELIST: &SYSTEM — Variable: use_all_frac

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `9d2723c614a363cdec3486d66e22f7ca96aac717279c7f448f784cafd95e16a7`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       use_all_frac
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    if (.FALSE.) force real-space FFT grids to be commensurate with
                   fractionary translations of non-symmorphic symmetry operations,
                   if present (e.g.: if a fractional translation (0,0,c/4) exists,
                   the FFT dimension along the c axis must be multiple of 4).
                   if (.TRUE.) do not impose any constraints to FFT grids, even in
                   the presence of non-symmorphic symmetry operations.
                   BEWARE: use_all_frac=.TRUE. may lead to wrong results for
                   hybrid functionals and phonon calculations. Both cases use
                   symmetrization in real space that works for non-symmorphic
                   operations only if the real-space FFT grids are commensurate.
   +--------------------------------------------------------------------
   
```
