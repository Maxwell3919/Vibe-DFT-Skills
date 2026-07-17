# INPUT_PW — NAMELIST: &RISM — Variable: starting3d

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `6212048c8201623942b9f68cdfcc6584e1314f58e491215702154834e46c2e5a`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       starting3d
   
   Type:           CHARACTER
   Description:   
                   'zero' :
                        Starting correlation functions of 3D-RISM from zero.
                        ( default for scf, *relax, *md )
    
                   'file' :
                        Start from existing "3d-rism_csuv_r.dat" file in the
                        directory specified by variables "prefix" and "outdir".
                        For nscf and bands calculation this is the default.
   +--------------------------------------------------------------------
   
```
