# INPUT_CP — NAMELIST: &WANNIER — Variable: wfsd

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `e966a67add1c1c12b90589f64754bc3b7cb016a993bf082feef613465d8bbee0`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wfsd
   
   Type:           INTEGER
   Default:        1
   Description:    Localization algorithm for Wannier function calculation:
                   wfsd=1  Damped Dynamics
                   wfsd=2  Steepest-Descent / Conjugate-Gradient
                   wfsd=3  Jocobi Rotation
                   Remember, this is consistent with all the calwf options
                   as well as the tolw (see below).
                   Not a good idea to Wannier dynamics with this if you are
                   using restart='from_scratch' option, since the spreads
                   converge fast in the beginning and ortho goes bananas.
   +--------------------------------------------------------------------
   
```
