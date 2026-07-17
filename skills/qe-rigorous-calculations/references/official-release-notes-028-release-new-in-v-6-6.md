# Quantum ESPRESSO release notes — New in v.6.6:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b829e618600198a9ffa616f6d58241917a6a3581b49cf63586abf9c143bbd9e6`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in v.6.6:
  * vdW-DF3-opt1, vdW-DF3-opt2, and vdW-DF-C6 van der Waals functionals
    implemented (T. Thonhauser, supported by NSF Grant No. 1712425)
  * More FORD documentation
  * Stress for non-collinear case
  * QE can be compiled on Windows 10 using PGI v.19.10 Community Edition
    configure works, except FoX: use script install/build_fox_with_pgi.sh
  * ParO and PPCG iterative diagonalization algorithms
  * Fourier interpolation of phonon potential implemented in ph.x
    (Jae-Mo Lihm, Seoul Natl. Univ.)
  * Extension of the PW code to DFT+U+V [JPCM 22, 055602 (2010)];
    Extension of the HP code to compute also inter-site Hubbard V parameters;
    Extension of the XSpectra code to work on top of DFT+U+V [arXiv:2004.04142]
    (I. Timrov, N. Marzari, M. Cococcioni).
    Extension of Hubbard forces and stress to ortho-atomic orbitals
    (I. Timrov, F. Aquilante, L. Binci, N. Marzari)
  * Support for BEEF-vdW XC (by Johannes Voss) compilation link has been included; 
    e.g. BEEF_LIBS="-L$LIBBEEF/src -lbeef", where $LIBBEEF is the path 
    to the compiled libbeef folder. If "calculation='ensemble'", 
    BEEF-vdW nscf ensemble energies will be generated at the end of PWscf.
    (Gabriel S. Gusmão, Georgia Tech)
  * i-PI socket now supports on-the-fly change of flags for SCF, forces,
    stresses and variable cell calculations using binary-integer enconding.
    (Gabriel S. Gusmão, Georgia Tech)
  * Phonon-induced electron self-energy implemented in ph.x and
    a new post-processing program PHonon/postahc.x added.
    (Jae-Mo Lihm, Seoul Natl. Univ.)
  * Implementation of the Sternheimer algorithm in the turboEELS code
    (O. Motornyi, N. Vast, I. Timrov, O. Baseggio, S. Baroni, and A. Dal Corso,
    Phys. Rev. B  102, 035156 (2020).)
  * EPW:
    (1) Use of the band manifold determined by Wannierization step
        when evaluating electron-phonon vertex on coarse grids
    (2) Support for PAW
    For the full list of new features and changes leading to backward incompatibility issues,
    please visit the Releases page of the EPW documentation site 
    [https://docs.epw-code.org/doc/Releases.html].
  
```
