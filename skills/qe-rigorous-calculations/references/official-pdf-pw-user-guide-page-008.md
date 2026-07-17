# pw_user_guide.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `e259f3a89eaa0822dec896739b1cefcf24d87c69a176ebfa95ac192c6845a547`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
you are interested in further processing of the results of non-SCF calculations (for instance,
in DOS calculations). In the latter case, you should specify a uniform grid of points. For
DOS calculations you should choose occupations=’tetrahedra’, together with an automat-
ically generated uniform k-point grid (card K POINTS with option “automatic”). Specify
nosym=.true. to avoid generation of additional k-points in low-symmetry cases. Variables
prefix and outdir, which determine the names of input or output files, should be the same
in the two runs. See examples 1, 6, 7.
    NOTA BENE: in non-scf calculations, the atomic positions are read by default from the
data file of the scf step, not from input.

Noncollinear magnetization, spin-orbit interactions The following input variables are
relevant for noncollinear and spin-orbit calculations:

     noncolin
     lspinorb
     starting magnetization (one for each type of atoms)

To make a spin-orbit calculation both noncolin and lspinorb must be true. Furthermore you
must use fully relativistic pseudopotentials at least for one atom. If all pseudopotentials are
scalar-relativistic, the calculation is noncollinear but there is no spin-orbit coupling.
    If starting magnetization is set to zero (or not given) the code makes a spin-orbit calcu-
lation without spin magnetization (it assumes that time reversal symmetry holds and it does
not calculate the magnetization). The states are still two-component spinors but the total
magnetization is zero.
    If starting magnetization is different from zero, the code makes a noncollinear spin po-
larized calculation with spin-orbit interaction. The final spin magnetization might be zero or
different from zero depending on the system. Note that the code will look only for symmetries
that leave the starting magnetization unchanged.
    See example 6 for noncollinear magnetism, example 7 (and references quoted therein) for
spin-orbit interactions.

DFT+U DFT+U (formerly known as LDA+U) calculation can be performed within a sim-
plified rotationally invariant form of the U Hubbard correction. Note that for all atoms having
a U value there should be an item in function Modules/set hubbard l.f90 and one in sub-
routine PW/src/tabd.f90, defining respectively the angular momentum and the occupancy of
the orbitals with the Hubbard correction. If your Hubbard-corrected atoms are not there, you
need to edit these files and to recompile.
    See example 8 and its README.

Dispersion Interactions (DFT-D) For DFT-D (DFT + semiempirical dispersion interac-
tions), see the description of input variable vdw corr and related input variables; sample input
files can be found in test-suite/pw vdw/vdw-d*.in. For DFT-D2, see also the comments
in source file Modules/mm dispersion.f90. For DFT-D3, see the README in the dft-d3/
directory.

Hartree-Fock and Hybrid functionals Hybrid functionals do not require anything special
to be done, but note that: 1) they are much slower than plain GGA calculations, 2) non-scf

                                               8
```
