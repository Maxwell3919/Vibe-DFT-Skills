# INPUT_PW — NAMELIST: &RISM — Variable: rism3d_conv_level

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `5086e0a3b0e56fd830f19ce2049a9aeb0cf17c4dc793733db276d4ac01d687ad`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       rism3d_conv_level
   
   Type:           REAL
   Default:        0.1 if "laue_both_hands" == .FALSE. .AND. "lgcscf" == .FALSE.;
                   0.3 if "laue_both_hands" == .FALSE. .AND. "lgcscf" == .TRUE.;
                   0.5 if "laue_both_hands" == .TRUE.
   Description:   
                   Convergence level of 3D-RISM.
    
                   0.0 :
                        Convergence level is 'low'.
                        Convergence threshold of 3D-RISM is greater than
                        "rism3d_conv_thr", when estimated energy error >> "conv_thr" .
                        The threshold becomes "rism3d_conv_thr", when
                        estimated energy error is enough small.
    
                   0.0<x<1.0 :
                        Convergence level is 'medium'.
                        Convergence threshold of 3D-RISM is intermediate value
                        between 'low' and 'high', where "rism3d_conv_level" is mixing rate.
    
                   1.0 :
                        Convergence level is 'high'.
                        Convergence threshold of 3D-RISM is always "rism3d_conv_thr" .
   +--------------------------------------------------------------------
   
```
