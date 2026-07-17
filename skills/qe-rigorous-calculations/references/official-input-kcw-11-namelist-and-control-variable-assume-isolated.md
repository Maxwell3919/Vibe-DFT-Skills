# INPUT_kcw — NAMELIST: &CONTROL — Variable: assume_isolated

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `315061c3661a6b1497157b6f8505d01dab858aea70ea997e0ad77d37c22af926`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       assume_isolated
   
   Type:           CHARACTER
   Default:        'none'
   Description:   
                   Used to perform calculation assuming the system to be
                   isolated (a molecule or a cluster in a 3D supercell).
                   
                   Currently available choices:
    
                   'none' :
                        (default): regular periodic calculation w/o any correction.
    
                   'martyna-tuckerman', 'm-t', 'mt' :
                        Martyna-Tuckerman correction
                        to both total energy and scf potential. Adapted from:
                        G.J. Martyna, and M.E. Tuckerman,
                        "A reciprocal space based method for treating long
                        range interactions in ab-initio and force-field-based
                        calculation in clusters", J. Chem. Phys. 110, 2810 (1999),
                        doi:10.1063/1.477923.
   +--------------------------------------------------------------------
   
```
