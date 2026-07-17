# INPUT_PW — NAMELIST: &CONTROL — Variable: dipfield

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `30d1b0a3ff8418e2d3670ebbfb6b3045189f175b9b9a00969da8c107beab65bc`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dipfield
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. and "tefield"==.TRUE. a dipole correction is also
                   added to the bare ionic potential - implements the recipe
                   of L. Bengtsson, PRB 59, 12301 (1999). See variables "edir",
                   "emaxpos", "eopreg" for the form of the correction. Must
                   be used ONLY in a slab geometry, for surface calculations,
                   with the discontinuity FALLING IN THE EMPTY SPACE.
   +--------------------------------------------------------------------
   
```
