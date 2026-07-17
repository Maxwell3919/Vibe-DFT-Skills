# INPUT_PW — NAMELIST: &RISM — Variable: rism3d_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `695b9958190b44b45e29dad22055df635bbd888f053c1d3e85ccbe7b7ba3034d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       rism3d_conv_thr
   
   Type:           REAL
   Default:        1.D-5 if "lgcscf" == .FALSE.;
                   5.D-6 if "lgcscf" == .TRUE.
   Description:    Convergence threshold for 3D-RISM.
   +--------------------------------------------------------------------
   
```
