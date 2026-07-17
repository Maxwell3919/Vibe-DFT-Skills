# INPUT_PW — NAMELIST: &ELECTRONS — Variable: mixing_mode

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ec0186ce3d551195fd4b944d259f8a494a0549673fff47480e6748a5242f58ae`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       mixing_mode
   
   Type:           CHARACTER
   Default:        'plain'
   Description:   
                   Available options are:
    
                   'plain' :
                        charge density Broyden mixing
    
                   'TF' :
                        as above, with simple Thomas-Fermi screening
                        (for highly homogeneous systems)
    
                   'local-TF' :
                        as above, with local-density-dependent TF screening
                        (for highly inhomogeneous systems)
   +--------------------------------------------------------------------
   
```
