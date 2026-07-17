# INPUT_BAND_INTERPOLATION — NAMELIST: &INTERPOLATION — Variable: method

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `c1bfb902df48ffaa341608ddd168a272e90274ed56fe65a36c5e7476f4fa1ef9`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       method
   
   Type:           CHARACTER
   Default:        'fourier-diff'
   Description:    The interpolation method to be used
   Description:   
                   Available options are:
    
                   'fourier-diff' :
                        band energies, as functions of k, are expanded in reciprocal space using a Star function basis set
                        (algorithm from Pickett W. E., Krakauer H., Allen P. B., Phys. Rev. B, vol. 38, issue 4, page 2721, 1988,
                         https://link.aps.org/doi/10.1103/PhysRevB.38.2721 ).
                        WARNING: The pwscf.xml file must be generated with "nosym" == .false. .
    
                   'fourier' :
                        band energies, as functions of k, are expanded in reciprocal space using a Star function basis set
                        (algorithm from D. D. Koelling, J. H. Wood, J. Comput. Phys., 67, 253-262 (1986).
                         https://ui.adsabs.harvard.edu/abs/1986JCoPh..67..253K ).
                        WARNING: The pwscf.xml file must be generated with "nosym" == .false. .
    
                   'idw' :
                        inverse distance weighting interpolation with Shepard metric
                        (ACM 68: Proceedings of the 1968 23rd ACM national conference, January 1968, Pages 517–524,
                         https://doi.org/10.1145/800186.810616 ).
                        WARNING: The pwscf.xml file must be generated with "nosym" == .true. .
                        WARNING: This method is REALLY simple and provides only a very rough estimate of the band structure.
    
                   'idw-sphere' :
                        inverse distance weighting interpolation inside a sphere of given radius.
                        WARNING: The pwscf.xml file must be generated with "nosym" == .true. .
                        WARNING: This method is REALLY simple and provides only a very rough estimate of the band structure.
   +--------------------------------------------------------------------
   
```
