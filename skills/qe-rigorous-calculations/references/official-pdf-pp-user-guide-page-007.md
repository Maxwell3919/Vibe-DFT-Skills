# pp_user_guide.pdf — page 7

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `2cab985ef57d9c31ecfd08cd60f411f36fef1ae6b924be42f38da0568877c3f1`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
  3. The wannier ham.x code generates a model Hamiltonian in Wannier functions basis: see
     PP/examples/WannierHam example/.

  4. The interface with Wannier90 code, wannier2pw.x: it builds Wannier functions as Hub-
     bard projectors for DFT+U

Note that the wfdd.x code has been moved to CP.

4.7    Interfaces to/from other code
Codes pw2bgw.x convert data files from pw.x to a format suitable for usage by the Berkeley GW
code. See file Doc/INPUT pw2bgw.* for input data documentation. Code bgw2pw.x, performing
the inverse conversion, no longer works: a copy that worked for the old file format is kept for
reference in bgw2pw.f90.orig.
     Code pw2gw.x converts data files from pw.x to a format suitable for usage by another
GW code, computes optical properties in single-particle approach (Fermi Golden Rule). See
file Doc/INPUT pw2gw.html for input data documentation, directory pw2gw example/ for an
example of usage.
     Code open grid.x writes Kohn-Sham orbitals for the complete k-point grid (not symmetry-
independent points only) in real space. Useful for further processing. It can be used to generate
the Kohn-Sham state data required in pw2wannier.x and Wannier90 from the initial SCF
calculation, bypassing the non-SCF calculation step.
     Code pw2critic.x is an interface to the CRITIC2 code by Alberto Otero-de-la-Roza. This
program creates a pwc file containing the Kohn-Sham orbitals from an SCF calculation (or from
the output of open grid.x). These orbitals are used for post-processing in CRITIC2.
     Code pw export.f90 no longer works and is no longer present.

4.8    Other tools
Exchange-correlation Code ppacf.x computes the coupling constant dependency of the
exchange correlation potential Exc,λ , λ ∈ [0 : 1] and the spatial distribution of the exchange-
correlation energy density and kinetic correlation energy density according to: Y. Jiao, E.
Schröder, and P. Hyldgaard, Phys. Rev. B 97, 085115 (2018). See PP/Doc/INPUT PPACF.html.

Wavefunction conversion Code wfck2r.x converts Kohn-Sham orbitals from reciprocal
to real space. It is a useful starting point if you need to access wavefunctions and perform
postprocessing operations that are not implemented in Quantum ESPRESSO.

Dielectric function Code epsilon.x calculates RPA frequency-dependent complex dielec-
tric function. Documentation is in file Doc/eps man.tex.

Core-level shifts Code initial state.x calculates the initial state contribution to the
Core-level shift. See CLS IS example/ for an example, and CLS FS example/ for the corre-
sponding final state calculation of Core-level shifts.




                                               7
```
