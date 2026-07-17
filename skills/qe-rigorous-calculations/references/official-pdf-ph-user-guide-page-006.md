# ph_user_guide.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `c6968fb4484f3475f4f2dcc317f7f9f6a9ef11cf8ec0a679846d22272d71aa97`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
done one q-vector at the time, a simpler procedure is to specify variable ldisp=.true. and to
set variables nq1, nq2, nq3 to some suitable Monkhorst-Pack grid, that will be automatically
generated, centered at q = 0.
    Second, code q2r.x reads the dynamical matrices produced in the preceding step and
Fourier-transform them, writing a file of Interatomic Force Constants in real space, up to a
distance that depends on the size of the grid of q-vectors. Input documentation in the header
of PHonon/PH/q2r.f90.
    Program matdyn.x may be used to produce phonon modes and frequencies at any q us-
ing the Interatomic Force Constants file as input. Input documentation in the header of
PHonon/PH/matdyn.f90.
    See Example 02 for a complete calculation of phonon dispersions in AlAs.

4.3    Calculation of electron-phonon interaction coefficients
Since v.5.0, there are two ways of calculating electron-phonon coefficients, distinguished accord-
ing to the value of variable electron phonon. The following holds for the case electron phonon=
’interpolated’ (see also Example 03).
    The calculation of electron-phonon coefficients in metals is made difficult by the slow conver-
gence of the sum at the Fermi energy. It is convenient to use a coarse k-point grid to calculate
phonons on a suitable wavevector grid; a dense k-point grid to calculate the sum at the Fermi
energy. The calculation proceeds in this way:

  1. a scf calculation for the dense k-point grid (or a scf calculation followed by a non-scf
     one on the dense k-point grid); specify option la2f=.true. to pw.x in order to save a
     file with the eigenvalues on the dense k-point grid. The latter MUST contain all k and
     k + q grid points used in the subsequent electron-phonon calculation. All grids MUST
     be unshifted, i.e. include k = 0.

  2. a normal scf + phonon dispersion calculation on the coarse k-point grid, specifying option
     electron phonon=’interpolated’, and the file name where the self-consistent first-order
     variation of the potential is to be stored: variable fildvscf). The electron-phonon coeffi-
     cients are calculated using several values of Gaussian broadening (see PHonon/PH/elphon.f90)
     because this quickly shows whether results are converged or not with respect to the k-
     point grid and Gaussian broadening.

  3. Finally, you can use matdyn.x and lambda.x (input documentation in the header of
     PHonon/PH/lambda.f90) to get the α2 F (ω) function, the electron-phonon coefficient λ,
     and an estimate of the critical temperature Tc .

    See the appendix for the relevant formulae. Important notice: the q → 0 limit of the con-
tribution to the electron-phonon coefficient diverges for optical modes! please be very careful,
consult the relevant literature.

4.4    DFPT with the tetrahedron method
In order to use the tetrahedron method for phonon calculations, you should run pw.x and ph.x
as follows:

  1. Run pw.x with occupation = "tetrahedra_opt" and K_POINT automatic.

                                                6
```
