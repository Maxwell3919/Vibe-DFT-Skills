# INPUT_PW — NAMELIST: &SYSTEM — Variable: exxdiv_treatment

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `f4e65a1c581c86b43a5e7ee5d05dfa391bb55bcc5c9fa0a434085b350ec6f1e5`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exxdiv_treatment
   
   Type:           CHARACTER
   Default:        'gygi-baldereschi'
   Description:   
                   Specific for EXX. It selects the kind of approach to be used
                   for treating the Coulomb potential divergencies at small q vectors.
    
                   'gygi-baldereschi' :
                        appropriate for cubic and quasi-cubic supercells
    
                   'vcut_spherical' :
                        appropriate for cubic and quasi-cubic supercells
                        (untested for non-orthogonal crystal axis)
    
                   'vcut_ws' :
                        appropriate for strongly anisotropic supercells, see also "ecutvcut"
                        (untested for non-orthogonal crystal axis)
    
                   'none' :
                        sets Coulomb potential at G,q=0 to 0.0 (required for GAU-PBE)
   +--------------------------------------------------------------------
   
```
