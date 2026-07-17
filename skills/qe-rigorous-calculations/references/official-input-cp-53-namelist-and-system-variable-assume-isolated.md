# INPUT_CP — NAMELIST: &SYSTEM — Variable: assume_isolated

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `ca59678e7f553f76704b7a8be46573ca4cb6f3726a7f7ace73c4d49917a41acc`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       assume_isolated
   
   Type:           CHARACTER
   Default:        'none'
   Description:    Used to perform calculation assuming the system to be
                           isolated (a molecule of a clustr in a 3D supercell).
                   
                           Currently available choices:
                   
                           'none' (default): regular periodic calculation w/o any correction.
                   
                           'makov-payne', 'm-p', 'mp' : the Makov-Payne correction to the
                                    total energy is computed.
                                    Theory:
                                    G.Makov, and M.C.Payne,
                                    "Periodic boundary conditions in ab initio
                                    calculations" , Phys.Rev.B 51, 4014 (1995)
                   
                   
                   var nextffield -type INTEGER {
                     default { 0 }
                     info {
                         Number of activated external ionic force fields.
                         See Doc/ExternalForceFields.tex for further explanation and parameterizations
                     }
                   }
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
