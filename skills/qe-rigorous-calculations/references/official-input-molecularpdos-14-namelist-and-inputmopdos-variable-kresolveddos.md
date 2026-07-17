# INPUT_molecularpdos — NAMELIST: &INPUTMOPDOS — Variable: kresolveddos

- Official source: https://www.quantum-espresso.org/Doc/INPUT_molecularpdos.txt
- Retrieved: 2026-07-17T11:49:57+00:00
- Official source SHA-256: `1e47fd2282c196dd8cfeb4de49502cedcb2fd40960784dcdc8b6955a6175cd8d`
- Extracted text SHA-256: `987747d37c79b71635598d3034fe2b2af1ee913bda660dfbb183e3dea29b6e2f`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       kresolveddos
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true. the k-resolved DOS is computed: not summed over
                   all k-points but written as a function of the k-point index.
                   In this case all k-point weights are set to unity
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================



:::: Notes

   
   ::: Format of output files
   
      Projections are written to standard output.
      
      The molecular projected DOS is written to the file "fileout".mopdos.
      
      * The format for the spin-unpolarized case is:
            index_of_molecular_orbital E MOPDOS(E)
            ...
      
      * The format for the collinear, spin-polarized case is:
            index_of_molecular_orbital E MOPDOSup(E) MOPDOSdw(E)
            ...
      
      The file "fileout".mopdos_tot contains the sum
      over the molecular orbitals.
      
      * The format for the spin-unpolarized case is:
            E MOPDOS(E)
            ...
      
      * The format for the collinear, spin-polarized case is:
            E MOPDOSup(E) MOPDOSdw(E)
            ...
      
      All DOS(E) are in states/eV plotted vs E in eV
      

   
   ::: Important notices
   
      * The atomic wavefunctions identified by the ranges
        i_atmwfc_beg_full:i_atmwfc_end_full (full system) and
        i_atmwfc_beg_part:i_atmwfc_end_part (molecular part)
        should correspond to the same atomic states. See the
        header of the output of projwfc.x for more information.
      
      * If using k-points, the same unit cell and the same
        k-points should be used in computing the molecular part,
        unless you really know what you are doing.
      
      * The tetrahedron method is presently not implemented.
      
      * Gaussian broadening is used in all cases
        (with ngauss and degauss values from input).
      


This file has been created by helpdoc utility on Wed Sep 03 14:28:58 CEST 2025
```
