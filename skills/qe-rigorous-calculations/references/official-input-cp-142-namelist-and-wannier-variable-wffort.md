# INPUT_CP — NAMELIST: &WANNIER — Variable: wffort

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `ccfbaf344c59709c0f6150c04d1d09d779a2a15be605391a03d6c6bcf51f8f32`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wffort
   
   Type:           INTEGER
   Default:        40
   Description:    This tells the code where to dump the orbital densities. Used
                    only with CALWF=1. for e.g. if you want to print 2 orbital
                    densities, set calwf=1, nwf=2 and wffort to an appropriate
                    number (e.g. 40) then the first orbital density will be
                    output to fort.40, the second to fort.41 and so on. Note that
                    in the current implementation, the following units are used
                    21,22,24,25,26,27,28,38,39,77,78 and whatever you define as
                    ndr and ndw. so use number other than these.
   +--------------------------------------------------------------------
   
```
