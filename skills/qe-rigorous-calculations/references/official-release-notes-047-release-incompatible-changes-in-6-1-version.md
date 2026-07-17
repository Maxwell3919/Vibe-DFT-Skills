# Quantum ESPRESSO release notes — Incompatible changes in 6.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `5695ec04f4644b0a5492001e866e8bfcc07ec0c6da86bb4bd4bcdf5097b303c4`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.1 version:

  * Routine h_psiq deleted, replaced by h_psi
  * Many variables related to tetrahedron method moved around
  * Functions set_sym and find_sym no longer require FFT grid dimensions as 
    input arguments, no longer force consistency of symmetries with FFT grids

Fixed in 6.1 version

  * TDDFPT: the keyword ltammd was missing in the namelist lr_dav
  * PW: real instead of complex constants in two ZGEMM calls could lead
        to NaN's in DFT_U forces with some compilers (e.g. PGI) (r13289)
  * pwi2xsf utility, also used in XCrysDen: various fixes (r13197)
  * PP: incorrect results in "projwfc.x" with PAW projection due to a missing
        line (r13121); crash in pw_export.x" due to dumb error (r13189);
        incorrect Fermi energy used in calculation of magnetic anisotropy
        with force theorem (r13335)
  * PW: final scf step in variable-cell calculation could crash
        due to missing reset of FFT dimensions (r13116)
  * FD: dangerous "q==0" check in matdyn.f90 (r13109)
  * Misc errors in new schema-based xml I/O (r13110, r13113)
  * CPV: stress and potential in nonlocal vdw-DF case were not correctly
         computed (r13102, r13143)
  * PWGui: double-hyphen glitch with old tcllib for NEB (r13101)
  * GWW wasn't working at all (r13099, r13100, r13106)
  * PW with hybrid functionals: 
    - LSDA with Gamma tricks and 2 pools did not work (r13158)
    - ACE energy slightly off, leading to crash, for metals (r13095)
      and for USPP (r13111)
    - small error in gamma-only USPP hybrid calculations using G space
      could lead to crashes (r13142)
  * Some Wyckoff site labels were incorrect (r13083, r13124)
    Also: symmetry analysis improved (r13094)
```
