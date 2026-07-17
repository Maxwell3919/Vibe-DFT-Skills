# INPUT_Q2R — NAMELIST: &INPUT — Variable: zasr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt
- Retrieved: 2026-07-17T11:49:50+00:00
- Official source SHA-256: `d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea`
- Extracted text SHA-256: `3622b2061a81eeb3b3f6e5c99bfc3b529a4d08b2e0266d1796dc74cc54e3de80`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       zasr
   
   Type:           CHARACTER
   Default:        'no'
   Description:   
                   Indicates the type of Acoustic Sum Rules used for the Born
                   effective charges.
                   
                   Allowed values:
    
                   'no' :
                        no Acoustic Sum Rules imposed (default)
    
                   'simple' :
                        previous implementation of the asr used
                        (3 translational asr imposed by correction of
                         the diagonal elements of the force-constants matrix)
    
                   'crystal' :
                        3 translational asr imposed by optimized
                        correction of the IFC (projection)
    
                   'one-dim' :
                        3 translational asr + 1 rotational asr
                        imposed by optimized correction of the IFC (the
                        rotation axis is the direction of periodicity; it
                        will work only if this axis considered is one of
                        the cartesian axis).
    
                   'zero-dim' :
                        3 translational asr + 3 rotational asr
                        imposed by optimized correction of the IFC.
    
                   Note that in certain cases, not all the rotational asr
                   can be applied (e.g. if there are only 2 atoms in a
                   molecule or if all the atoms are aligned, etc.).
                   In these cases the supplementary asr are cancelled
                   during the orthonormalization procedure (see below).
   +--------------------------------------------------------------------
   
```
