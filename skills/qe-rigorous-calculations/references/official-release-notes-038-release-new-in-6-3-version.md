# Quantum ESPRESSO release notes — New in 6.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b7db9312a3577d2cbe27f25d12e1f4a73bb08bb0d30fae9940b48d8fea5471f1`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.3 version:
  * New implementation, using  a more robust algorithm for the Wigner-Seitz 
    construction in EPW (Samuel Ponce and Carla Verdi) 
  * New application for optical spectra computation using optimized basis sets 
   (Paolo Umari, Nicola Marzari and Giovanni Prandini).  

  * Improved interface between TDDFPT and Environ using plugins( Oliviero Andreussi)  

  * Improved FFT threading (Ye Luo, Argonne)

  * EXX: ACE can be projected on arbitrary number of orbitals
    Slight change in SCF convergence with ACE (dexx) properly
    accounting for difference between 2*<new|V(old)|new> 
    and <new|V(old)|new> + <old|V(new)|old>  (see "fock3" term) 
    SCDM and localized exchange is now compatible with ecutfock
    Localized exchange can deal with virtual orbitals (empty bands)
    (Ivan Carnimeo)

  * Spin-polarized X3LYP (experimental)

  * EPW: Electronic transport (Boltzmann transport equation)
         Iterative Boltzmann transport equation (experimental)
         Improved way to compute Wigner-Seitz vectors 
         Cumulant treatement (model)
         Possible screening
         Support for exclude bands
         Calculation of velocity beyond the local approximation (experimental)

Problems fixed in 6.3 version:

  * Stress with hybrid functionals and Gamma point was grossly wrong
    (5ed148646)

  * EPW: Velocity in the dipole approximation was unstable because of 
    G-vector ordering. 

  * Real-space augmentation functions were crashing with -nt N option

  * Calculation of ELF wasn't always working due to a bad usage of FFT
    descriptors - noticed by Enrique Zanardi Maffiotte (commit a86fb75d)

  * Workaround for gfortran bug in FoX (commit 5b36b697) and for pgi+openmp
    bug (f43e72c9)

  * Reading of starting wavefunctions from file, including restart case,
    wasn't always working as expected. This might be at the origin of
    mysterious "davcio errors" (April 18, 2018)

  * Parameters for electric fields were not saved to the new XML file, thus
    breaking some forms of postprocessing (noticed by Thomas Brumme and 
    Giovanni Cantele, fixed April 18, 2018)

  * Bug in reading (with FoX) the augmentation part of pseudopotentials in
    upf v.2 format. The bug shows up only for PPs generated using David
    Vanderbilt's code, yielding a mysterious message "Error in scalartorealdp
    Too few elements found" (March 20, 2018)

  * LDA+U for spin-orbit (kind=1) was crashing for one k-point, trying to read
    data not previously saved (noticed by Christof Wolf, Feb 8, 2018)

  * ibrav =-13 wasn't documented and did not recognize the correct parameter
    cosBC (noticed by Jose' Conesa, Jan 26, 2018)

  * Yet another problem with the final scf step in a vc-relax calculation: if
    restarted from an interrupted calculation, the final step was trying to
    read the charge density with a different number of G-vectors (Jan 23, 2018)

  * CP with LDA+U: the choice of the LDA+U manifolds from atomic wavefunctions
    was sometimes not working properly due to a missing check (Jan 22, 2018)

  * pw2bgw.x fixed, courtesy G. Samsonidze (Jan.16, 2018)

  * Band parallelization was broken in one of the last commits
    just before v.6.2.1 (Dec.23, 2017)

  * TDDFPT in "lr_addus_dvpsi.f90" had a bug for systems with USPP
    and more than 2 atoms (Dec.22, 2017) (Oleksandr Motornyi, 
    Michele Raynaud, Iurii Timrov, Nathalie Vast, Andrea Dal Corso)

  * Phonons with images wasn't working in v.6.2.1 with old PP files
    containing "&" in the header section (Dec.20, 2017)

  * PWscf in "manypw" mode wasn't working due to a bad IF (Dec.12, 2017)
```
