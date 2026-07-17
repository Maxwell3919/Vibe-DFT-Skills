# INPUT_DYNMAT — NAMELIST: &INPUT — Variable: asr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DYNMAT.txt
- Retrieved: 2026-07-17T11:49:10+00:00
- Official source SHA-256: `4da654f7ed8ec6ceb5d38a4e470389b2fb414999eb5233e083ea454c2669470e`
- Extracted text SHA-256: `fab4476d73826784961c40b04bafbc3f12e52521faee68db4d59d75d5ed1e493`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       asr
   
   Type:           CHARACTER
   Default:        'no'
   Description:   
                   Indicates the type of Acoustic Sum Rule imposed.
                   
                   Allowed values:
    
                   'no' :
                        no Acoustic Sum Rules imposed (default)
    
                   'simple' :
                        previous implementation of the asr used
                        (3 translational asr imposed by correction of
                         the diagonal elements of the dynamical matrix)
    
                   'crystal' :
                        3 translational asr imposed by optimized
                        correction of the dyn. matrix (projection)
    
                   'one-dim' :
                        3 translational asr + 1 rotational asr imposed
                        by optimized correction of the dyn. mat. (the
                        rotation axis is the direction of periodicity; it
                        will work only if this axis considered is one of
                        the Cartesian axis).
    
                   'zero-dim' :
                        3 translational asr + 3 rotational asr imposed
                        by optimized correction of the dyn. mat.
    
                   Note that in certain cases, not all the rotational asr
                   can be applied (e.g. if there are only 2 atoms in a
                   molecule or if all the atoms are aligned, etc.).  In
                   these cases the supplementary asr are canceled during
                   the orthonormalization procedure (see below).
                   
                   Finally, in all cases except 'no' a simple correction
                   on the effective charges is performed (same as in the
                   previous implementation).
   +--------------------------------------------------------------------
   
```
