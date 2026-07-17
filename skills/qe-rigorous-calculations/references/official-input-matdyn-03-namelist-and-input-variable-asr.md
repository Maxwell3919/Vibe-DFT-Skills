# INPUT_MATDYN — NAMELIST: &INPUT — Variable: asr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `e5a87bf4709c5e5abbb8e6aad2eaadac3590b36f7476bb9acb6d5866bf791de4`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
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
                         the diagonal elements of the force constants matrix)
    
                   'crystal' :
                        3 translational asr imposed by optimized
                        correction of the force constants (projection)
    
                   'all' :
                        3 translational asr + 3 rotational asr + 15 Huang
                        conditions for vanishing stress tensor, imposed by
                        optimized correction of the force constants (projection).
                        Remember to set write_lr = .true. to write long-range
                        force constants into file when running q2r and set "read_lr" = .true. when running matdyn in the case of
                        infrared-active solids. (See npj Comput Mater 8, 236 (2022))
    
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
                   molecule or if all the atoms are aligned, etc.).
                   In these cases the supplementary asr are cancelled
                   during the orthonormalization procedure (see below).
   +--------------------------------------------------------------------
   
```
