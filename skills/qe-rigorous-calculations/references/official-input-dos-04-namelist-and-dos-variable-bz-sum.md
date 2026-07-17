# INPUT_DOS — NAMELIST: &DOS — Variable: bz_sum

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DOS.txt
- Retrieved: 2026-07-17T11:49:09+00:00
- Official source SHA-256: `d18fa270d3ca41b3bed586c40bb9cf5fb2b67962e741381a75bea23b6601eff3`
- Extracted text SHA-256: `a902a02fc7c622968cd105d8a75f9749d9f61283da975013ffa120652aac3ffe`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       bz_sum
   
   Type:           CHARACTER
   Description:   
                   Keyword selecting  the method for BZ summation. Available options are:
    
                   'smearing' :
                        integration using gaussian smearing. In fact currently
                        any string not related to tetrahedra defaults to smearing;
    
                   'tetrahedra' :
                        Tetrahedron method, Bloechl's version:
                        P.E. Bloechl, PRB 49, 16223 (1994)
                        Requires uniform grid of k-points, to be
                        automatically generated in pw.x.
    
                   'tetrahedra_lin' :
                        Original linear tetrahedron method.
                        To be used only as a reference;
                        the optimized tetrahedron method is more efficient.
    
                   'tetrahedra_opt' :
                        Optimized tetrahedron method:
                        see M. Kawamura, PRB 89, 094515 (2014).
   Default:        'smearing' if degauss is given in input;
                                           options read from the xml data file otherwise.
   +--------------------------------------------------------------------
   
```
