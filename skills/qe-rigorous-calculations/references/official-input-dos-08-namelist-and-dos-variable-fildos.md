# INPUT_DOS — NAMELIST: &DOS — Variable: fildos

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DOS.txt
- Retrieved: 2026-07-17T11:49:09+00:00
- Official source SHA-256: `d18fa270d3ca41b3bed586c40bb9cf5fb2b67962e741381a75bea23b6601eff3`
- Extracted text SHA-256: `0d556e03b5caea8432644b6a872552b1dacc508f1926fa3971c456f7a2164432`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       fildos
   
   Type:           CHARACTER
   Default:        '"prefix".dos'
   Description:    output file containing DOS(E)
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================



:::: Notes

   
   ::: Output
   
      The total DOS (states/eV plotted vs E in eV) is written to file "fildos"
      

   
   ::: Important !
   
      The tetrahedron method is used if
      
          - the input data file has been produced by pw.x using the option
            occupations='tetrahedra', AND
      
          - a value for degauss is not given as input to namelist &dos
      
      
      Gaussian broadening is used in all other cases:
      
          - if "degauss" is set to some value in namelist &DOS, that value
            (and the optional value for "ngauss") is used
      
          - if "degauss" is NOT set to any value in namelist &DOS, the
            value of "degauss" and of "ngauss" are read from the input data
            file (they will be the same used in the pw.x calculations)
      
          - if "degauss" is NOT set to any value in namelist &DOS, AND
            there is no value of "degauss" and of "ngauss" in the input data
            file, "degauss"="DeltaE" (in Ry) and "ngauss"=0 will be used
      


This file has been created by helpdoc utility on Wed Sep 03 14:28:58 CEST 2025
```
