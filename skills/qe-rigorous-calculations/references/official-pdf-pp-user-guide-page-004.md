# pp_user_guide.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `b4336f35b4a2801deae1c2969590cd83577a301ac8f7414feaafd891d56c82c7`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   Quantities that can be read or calculated are:

      charge density
      spin polarization
      various potentials
      local density of states at EF
      local density of electronic entropy
      STM images
      selected squared wavefunction
      ELF (electron localization function)
      RDG (reduced density gradient)
      integrated local density of states

Various types of plotting (along a line, on a plane, three-dimensional, polar) and output formats
(including the popular cube format) can be specified. Moreover data can be saved to an
intermediate (formatted) file so that more data sets can be summed or subracted in a later
run. The output files can be directly read by the free plotting system Gnuplot (1D or 2D
plots), or by code plotrho.x that comes with PostProc and produces PostScript 2D plots, or
by advanced plotting software XCrySDen (3D plots).
    See file PP/Doc/INPUT PP.* for a detailed description of the input for code pp.x. See
Example 01 for an example of a charge density plot, Example 03 for an example of STM image
simulation.

Planar averages Code plan avg.x calculates planar averages of Kohn-Sham orbitals. Input
documentation is in the header ofPP/src/plan avg.f90.
   Code average.x calculates planar averages of quantities produced by pp.x (e.g. potentials,
charge, magnetization densities). Note that average.x reads the intermediate file produced
by pp.x, not data files produced by pw.x. Examples of usage of average.x can be found in
PP/examples/WorkFct example/ and in PP/examples/dipole example/.

All-electron charge pawplot.x produces plots of the all-electron charge for PAW calcula-
tions. Input documentation in the header of PP/src/pawplot.f90.

4.2    About Bader’s analysis
In http://theory.cm.utexas.edu/henkelman/code/bader/ one can find a software that per-
forms Bader’s analysis starting from charge on a regular grid. One should use PAW to compute
the charge density. The required ”cube” format can be produced using pp.x (info by G.
Lapenna who has successfully used this technique, but adds: “Problems occur with polar X-H
bonds or in all cases where the zero-flux of density comes too close to atoms described with
pseudo-potentials”). This code should perform decomposition into Voronoi polyhedra as well,
in place of obsolete code voronoy.x (removed from distribution since v.4.2). Alternatively, you
can use CRITIC2, available at https://github.com/aoterodelaroza/critic2, which can
read directly pw.x output and “XSF” files. CRITIC2 functionaly include Bader’s AIM, ELF,
laplacian of density and potentials, non-covalente interaction (NCI) plots and much more.




                                               4
```
