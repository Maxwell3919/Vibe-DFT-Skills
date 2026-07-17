# Quantum ESPRESSO release notes — New in 6.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `8fad0c44f92145c86eb2900a1173e3ec3757193e5660368b468dc21526f80181`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.2 version:

  * SCAN functional with libxc v.3; bands with meta-GGA can be computed
   (Davide Ceresoli)

  * EXX with localization (experimental)

  * Stress calculation is enabled in ESM
    “starting_charge” option added to SYSTEM namelist

  * Unscreened hybrid vdW-DF (JCP 146, 234106 (2017), contributed by 
    Per Hyldgaard and Jeff Neaton

Fixed in 6.2 version

  * DFPT with constrained magnetization for insulators wasn't working
    (r13915)

  * virtual.x was linking a duplicate obsolete "pseudo" module, leading to
    "unrecognized dft" error (fix provided by Stefano Dal Forno, r13910)

  * NEB + EXX works again (r13851)

  * Under some circumstances (k-points, reduced ecutfock, other unclear  
    reasons), EXX with reduced cutoff wasn't giving accurate results, 
    due to a mismatch between the ordering of G-vectors in the original 
    FFT grid and in the grid for ecutfock. Also fixed: incorrect indices
    of -G (used in Gamma-only case) when nr1 /= nr2 (r13833)

  * Variable-cell glitches: with EXX, G-vectors used in the FFT of 1/|r-r'|
    should be rescaled as well (courtesy Satomichi Nisihara) (r13817);
    with tetrahedra, deallocation must be done only at the end (r13932).

  * Bug in DFPT with tetrahedra and in "fermisurfer", plus some extensions
    to el-ph with tetrahedra (Mitsuaki Kawamura) (r13806).

  * EXX with k-points and pool parallelization was occasionally crashing
    due to questionable custom FFT grid initialization (r13728+r13835)

  * ESM energy and forces for 'bc2' case and nonzero esm_efield were not
    correct (r13727). Also: problem with restart in NEB with ESM fixed

  * __USE_3D_FFT was broken since v.6.0 (r13700, r13706)

  * Some constants in the definition of PBE functionals were truncated to 
    6 significant digits. While not a bug, this could lead to tiny differences
    with respect to previous results and other XC implementations (r13592)

  * Examples for magnetic anisotropy with force theorem were not properly
    updated (r13534)

  * Orthogonalization of Hubbard manifold in LDA+U with non-default values
    of U_projection_type was not properly done in v.6.0 and 6.1 (r13529)
    Thanks to Andrea Ferretti and Mike Atambo for fixing this.

  * Bug in parallel FFT when task groups are used and the number of XY planes 
    is not a multiple of the number of MPI tasks and of task groups (r13489)

  * Born effective charges with "Zeu" method were not correctly computed 
    when both GGA and core corrections were present (r13474 and r13481).
    Thanks to Vineet Kumar Pandey for reporting the problem.

  * reset_grid wasn't resetting grid properly if k1,k2,k3=0. Thanks to
    Giuliana Barbarino (r13462)

  * EXX in non-collinear/spin-orbit case wasn't correct (r13453)

  * Fixed a small bug in two subroutines only called by Environ (r13451)

  * Out-of-bounds error in hybrid functionals with LSDA, Gamma tricks and
    2 pools (r13448)

  * EPW: in v.6.1 there was a mismatch between symmetry operations in PW
    and in EPW. It affected results of v.6.1 only in the presence of
    fractional translations incommensurate with the FFT grid. (r13443)

  * FFTXlib: the case in which the smooth and dense grids have the same FFT
    dimensions along x and y but different along z was incorrectly treated,
    leading to strange error messages. (r13439 and r13445)

  * There was a small inconsistency in the vdW-DF kernel generating routine
    "generate_vdW_kernel_table.f90", not affecting in any significant way 
    the results. It is anyway recommended to re-generate the kernel file.
    Thanks to C.Y. Ren for noticing this. (r13438)
```
