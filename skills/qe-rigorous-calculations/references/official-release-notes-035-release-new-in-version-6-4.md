# Quantum ESPRESSO release notes — New in version 6.4:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `a6a99d1161c7bf4a4792027ba9e79859ab9a8cfb458f5146d8d4fbf676bdd2d8`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in version 6.4:
  * Experimental version of SCDM localization with k-points, activated like for
    k=0 by specifying in &system namelist a value > 0 for "localization_thr".
  * It is now possible to limit the number of xml step elements printed out
    for relaxation or molecular dynamics simulation, by setting the environment
    variable MAX_XML_STEPS. Useful in case of very long trajectories to avoid 
    issues due to too large file size.  
  * EPW works with ultrasoft pseudopotentials (F. Giustino, S. Poncé, R. Margine)
  * New code hp.x to compute Hubbard parameters using density-functional
    perturbation theory (experimental stage) (I. Timrov, N. Marzari, and M. Cococcioni, 
    Phys. Rev. B 98, 085127 (2018); arXiv:1805.01805)
  * The PHonon code works with the Hubbard U correction (experimental stage)
    (A. Floris, S. de Gironcoli, E.K.U. Gross, and M. Cococcioni,
    Phys. Rev. B 84, 161102(R) (2011);
    A. Floris, I. Timrov, B. Himmetoglu, N. Marzari, S. de Gironcoli,
    and M. Cococcioni, in preparation)
  * XDM now works also for USPP and norm-conserving PP

Problems fixed in version 6.4 (+ = in qe-6.3-backports as well) :
  + Codes reading scf data recomputed celldm parameters also if ibrav=0
    This produced confusing output and had the potential to break some codes
  + index not correctly initialized in LSDA phonon with core corrections 
  + GTH pseudopotentials in analytical form wrongly computed in some cases
  + projwfc.x not working with new xml format in non-collinear/spinorbit case 
  + Starting with .EXIT file present ("dry run") crashed with new file format
  + Some space groups were missing
  + Random MPI crashes with DFT+U due to small discrepancies between values
    of Hubbard occupancies on different processors
  + Variable-cell optimization wasn't working with Tkatchenko-Scheffler vdW
  + Atomic occupancies for DFT+U were not correctly written by CP after 
    switch to new format, due to a mismatch in their definition
  + Phonons with option "nosym" wasn't working
  + Option "noinv" wasn't read from new xml file
  * Variable-cell optimization with hybrid functionals wasn't working due
    to missing re-initialization (it also crashed during the final scf step)
  + Printout of wall time was sometimes incorrect (courtesy Daniel Pinkal)
  + 'make install' and 'make -jN' cases fixed (maybe)
  + The restart option in turboEELS (turbo_eels.x) with ultrasoft
    pseudopotentials was not working.
  + bad format in upf%comment when writing the PP_INFO section of UPF v2 PPs
```
