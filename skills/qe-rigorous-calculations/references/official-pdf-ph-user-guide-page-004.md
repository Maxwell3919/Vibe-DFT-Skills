# ph_user_guide.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `d859c7aeae2a396dfdc4f47019940305fea4852834d7884572dfe04fbd36f2ea`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    Note: since v.5.4, packages PlotPhon (for phonon plotting) and QHA (vibrational free energy
in the Quasi-Harmonic approximations), contribute by the late Prof. Eyvaz Isaev, are no longer
bundled with PHonon. Their latest version can be found in the tarballs of v.5.3 of QE.

3.2    Compilation
Typing make ph from the root Quantum ESPRESSO directory, or make from the PHonon
directory, produces the following codes:

     PH/ph.x: Calculates phonon frequencies and displacement patterns, dielectric tensors,
      effective charges (uses data produced by pw.x).

     PH/dynmat.x: applies various kinds of Acoustic Sum Rule (ASR), calculates LO-TO
      splitting at q = 0 in insulators, IR and Raman cross sections (if the coefficients have been
      properly calculated), from the dynamical matrix produced by ph.x

     PH/q2r.x: calculates Interatomic Force Constants (IFC) in real space from dynamical
      matrices produced by ph.x on a regular q-grid

     PH/matdyn.x: produces phonon frequencies at a generic wave vector using the IFC file
      calculated by q2r.x; may also calculate phonon DOS, the electron-phonon coefficient λ,
      the function α2 F (ω)

     PH/lambda.x: also calculates λ and α2 F (ω), plus Tc for superconductivity using the
      McMillan formula

     PH/alpha2f.x: also calculates λ and α2 F (ω). It is used together with the optimized
      tetrahedron method and shifted q-grid

     PH/fqha.x: a simple code to calculate vibrational entropy with the quasi-harmonic ap-
      proximation

     PH/dvscf q2r.x: performs inverse Fourier transformation of phonon potential from a
      regular q grid to real space.

     Gamma/phcg.x: a version of ph.x that calculates phonons at q = 0 using conjugate-
      gradient minimization of the density functional expanded to second-order. Only the Γ
      (k = 0) point is used for Brillouin zone integration. It is faster and takes less memory
      than ph.x, but does not support spin polarization, USPP and PAW.

Links to the main Quantum ESPRESSO bin/ directory are automatically generated.


4     Using PHonon
Phonon calculation is presently a two-step process. First, you have to find the ground-
state atomic and electronic configuration; Second, you can calculate phonons using Density-
Functional Perturbation Theory. Further processing to calculate Interatomic Force Constants,
to add macroscopic electric field and impose Acoustic Sum Rules at q = 0 may be needed. In
the following, we will indicate by q the phonon wavevectors, while k will indicate Bloch vectors
used for summing over the Brillouin Zone.

                                                4
```
