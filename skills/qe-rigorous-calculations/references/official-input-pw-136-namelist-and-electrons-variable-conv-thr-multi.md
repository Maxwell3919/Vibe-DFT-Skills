# INPUT_PW — NAMELIST: &ELECTRONS — Variable: conv_thr_multi

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `846625f0d13feee81ee10c8ff93f8261a21792887777d2c1be76f1b10fd3f630`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       conv_thr_multi
   
   Type:           REAL
   Default:        1.D-1
   Description:    When "adaptive_thr" = .TRUE. the convergence threshold for
                   each scf cycle is given by:
                   max( "conv_thr", "conv_thr_multi" * dexx )
   +--------------------------------------------------------------------
   
```
