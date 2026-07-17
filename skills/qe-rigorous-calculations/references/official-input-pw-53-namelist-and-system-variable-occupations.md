# INPUT_PW — NAMELIST: &SYSTEM — Variable: occupations

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `f874b35bf0bf97cb5d3bae7df9cab870ed44775604287ca064036ef1dea4fb1d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       occupations
   
   Type:           CHARACTER
   Description:   
                   Available options are:
    
                   'smearing' :
                        gaussian smearing for metals;
                        see variables "smearing" and "degauss"
    
                   'tetrahedra' :
                        Tetrahedron method, Bloechl's version:
                        P.E. Bloechl, PRB 49, 16223 (1994)
                        Requires uniform grid of k-points, to be
                        automatically generated (see card "K_POINTS").
                        Well suited for calculation of DOS,
                        less so (because not variational) for
                        force/optimization/dynamics calculations.
    
                   'tetrahedra_lin' :
                        Original linear tetrahedron method.
                        To be used only as a reference;
                        the optimized tetrahedron method is more efficient.
    
                   'tetrahedra_opt' :
                        Optimized tetrahedron method:
                        see M. Kawamura, PRB 89, 094515 (2014).
                        Can be used for phonon calculations as well.
    
                   'fixed' :
                        for insulators with a gap
    
                   'from_input' :
                        The occupation are read from input file,
                        card "OCCUPATIONS". Option valid only for a
                        single k-point, requires "nbnd" to be set
                        in input. Occupations should be consistent
                        with the value of "tot_charge".
   +--------------------------------------------------------------------
   
```
