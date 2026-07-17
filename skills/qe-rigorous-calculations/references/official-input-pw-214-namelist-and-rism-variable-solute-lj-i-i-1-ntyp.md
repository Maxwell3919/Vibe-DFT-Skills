# INPUT_PW — NAMELIST: &RISM — Variable: solute_lj(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ae58688ff366032df75e4eba27aaf311308f4c0a40650015da3feac2552d446c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       solute_lj(i), i=1,ntyp
   
   Type:           CHARACTER
   Default:        'uff'
   Description:   
                   Specify the Lennard-Jones potential of solute on atomic type 'i':
    
                   'none' :
                        The Lennard-Jones potential is not specified here.
                        you must set "solute_epsilon" and "solute_sigma".
    
                   'uff' :
                        Universal Force Field.
                        [A.K.Rappe et al., JACS 144, 10024 (1992), doi:10.1021/ja00051a040]
    
                   'clayff' :
                        Clay's Force Field
                        [R.T.Cygan et al., JPC B 108, 1255 (2004), doi:10.1021/jp0363287]
    
                   'opls-aa' :
                        OPLS-AA (generic parameters for QM/MM)
   +--------------------------------------------------------------------
   
```
