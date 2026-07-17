# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: plotboxes

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `cdfb8c32012e9afadba8292a730e74eccf61d40fbe0528181e75bd8d77f72d50`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       plotboxes
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true., the boxes are written in output as xsf files with
                   3D datagrids, valued 1.0 inside the box volume and 0 outside
                   (visualize them as isosurfaces with isovalue 0.5)
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================



:::: Notes

   
   ::: Format of output files
   
      Projections are written to standard output, and also to file
      "filproj" if given as input.
      
      The total DOS and the sum of projected DOS are written to file
      "filpdos".pdos_tot.
      
      * The format for the collinear, spin-unpolarized case and the
        non-collinear, spin-orbit case is:
            E DOS(E) PDOS(E)
            ...
      
      * The format for the collinear, spin-polarized case is:
            E DOSup(E) DOSdw(E)  PDOSup(E) PDOSdw(E)
            ...
      
      * The format for the non-collinear, non spin-orbit case is:
            E DOS(E) PDOSup(E) PDOSdw(E)
            ...
      
      In the collinear case and the non-collinear, non spin-orbit case
      projected DOS are written to file "filpdos".pdos_atm#N(X)_wfc#M(l),
      where N = atom number , X = atom symbol, M = wfc number, l=s,p,d,f
      (one file per atomic wavefunction found in the pseudopotential file)
      
      * The format for the collinear, spin-unpolarized case is:
            E LDOS(E) PDOS_1(E) ... PDOS_2l+1(E)
            ...
        where LDOS = \sum m=1,2l+1 PDOS_m(E)
        and PDOS_m(E) = projected DOS on atomic wfc with component m
      
      * The format for the collinear, spin-polarized case and the
        non-collinear, non spin-orbit case is as above with
        two components for both  LDOS(E) and PDOS_m(E)
      
      In the non-collinear, spin-orbit case (i.e. if there is at least one
      fully relativistic pseudopotential) wavefunctions are projected
      onto eigenstates of the total angular-momentum.
      Projected DOS are written to file "filpdos".pdos_atm#N(X)_wfc#M(l_j),
      where N = atom number , X = atom symbol, M = wfc number, l=s,p,d,f
      and j is the value of the total angular momentum.
      In this case the format is:
          E LDOS(E) PDOS_1(E) ... PDOS_2j+1(E)
          ...
      
      If "kresolveddos"=.true., the k-point index is prepended
      to the formats above, e.g. (collinear, spin-unpolarized case)
          ik E DOS(E) PDOS(E)
      
      All DOS(E) are in states/eV plotted vs E in eV
      

   
   ::: Orbital Order
   
      Order of m-components for each l in the output:
      
          1, cos(phi), sin(phi), cos(2*phi), sin(2*phi), .., cos(l*phi), sin(l*phi)
      
      where phi is the azimuthal angle: x=r cos(theta)cos(phi), y=r cos(theta)sin(phi)
      This is determined in file upflib/ylmr2.f90 that calculates spherical harmonics.
      
      for l=1:
        1 pz     (m=0)
        2 px     (real combination of m=+/-1 with cosine)
        3 py     (real combination of m=+/-1 with sine)
      
      for l=2:
        1 dz2    (m=0)
        2 dzx    (real combination of m=+/-1 with cosine)
        3 dzy    (real combination of m=+/-1 with sine)
        4 dx2-y2 (real combination of m=+/-2 with cosine)
        5 dxy    (real combination of m=+/-2 with sine)
      

   
   ::: Defining boxes for the Local DOS(E)
   
      Boxes are specified using the variables "irmin" and "irmax":
      
      FFT grid points are included from irmin(j,n) to irmax(j,n)
      for j=1,2,3 and n=1,...,"n_proj_boxes"
      
      "irmin" and "irmax" range from 1 to nr1 or nr2 or nr3
      
      Values larger than nr1/2/3 or smaller than 1 are folded
      to the unit cell.
      
      If "irmax"<"irmin" FFT grid points are included from 1 to irmax
      and from irmin to nr1/2/3.
      

   
   ::: Important notices
   
      The tetrahedron method is used if
      
          - the input data file has been produced by pw.x using the option
            occupations='tetrahedra', AND
      
          - a value for degauss is not given as input to namelist &projwfc
      
      * Gaussian broadening is used in all other cases:
      
          - if "degauss" is set to some value in namelist &PROJWFC, that value
            (and the optional value for ngauss) is used
      
          - if "degauss" is NOT set to any value in namelist &PROJWFC, the
            value of "degauss" and of "ngauss" are read from the input data
            file (they will be the same used in the pw.x calculations)
      
          - if "degauss" is NOT set to any value in namelist &PROJWFC, AND
            there is no value of "degauss" and of "ngauss" in the input data
            file, "degauss"="DeltaE" (in Ry) and "ngauss"=0 will be used
      
      
      Obsolete variables, ignored:
          io_choice
          smoothing
      


This file has been created by helpdoc utility on Wed Sep 03 14:29:00 CEST 2025
```
