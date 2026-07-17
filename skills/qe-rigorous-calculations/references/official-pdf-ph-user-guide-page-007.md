# ph_user_guide.pdf — page 7

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `dcc862e3a470b4ed3fbfc455987c6ef7eaf0350585914c83d837bbcd1ec43aa5`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
  2. Run ph.x.
   There is an example in PHonon/example/tetra_example/.

4.5    Calculation of electron-phonon interaction coefficients with the
       tetrahedron method
When you perform a calculation of electron-phonon interaction coefficients with the tetrahedron
method, you have to use an offset q-point grid in order to avoid a singularity at q = Γ; you can
perform this calculation as follows:

  1. Run pw.x with occupation = "tetrahedra_opt" and K_POINT automatic.

  2. Run ph.x with lshift_q = .true. and electron_phonon = "" (or unset it) to generate
     the dynamical matrix and the deformation potential (in _ph*/{prefix}_q*/) of each q.

  3. Run ph.x with electron_phonon = "lambda_tetra". You should use a denser k grid
     by setting nk1, nk2, and nk3. Then lambda*.dat are generated; they contain λqν .

  4. Run alpha2f.x with an input file as follows:

      &INPUTPH
      ! The same as that for the electron-phonon calculation with ph.x
       :
      /
      &INPUTA2F
        nfreq = Number of frequency-points for a2F(omega),
      /

      Then λ, and ωln are computed and they are printed to the standard output. α2 F (ω) and
      (partial) phonon-DOS are also computed; they are printed to a file prefix .a2F.dat.

   There is an example in PHonon/example/tetra_example/.

4.6    Phonons for two-dimensional crystals
The extension of DFPT to two dimensional crystals, in particular gated two-dimensional het-
erostructure, s described in the following paper:
   T. Sohier, M. Calandra, and F. Mauri, Phys. Rev. B 96, 075448 (2017), https://doi.org/10.1103/Phy
   See example PHonon/example/example17/.

4.7    Phonons from DFPT+U
The extension of DFPT to inlcude Hubbard U correction is described in the following papers:
   A. Floris, S. de Gironcoli, E. K. U. Gross, M. Cococcioni, Phys. Rev. B 84, 161102(R),
(2011);
   A. Floris, I. Timrov, B. Himmetoglu, N. Marzari, S. de Gironcoli, and M. Cococcioni, Phys.
Rev. B 101, 064305 (2020).
   See example PHonon/example/example18/.

                                               7
```
