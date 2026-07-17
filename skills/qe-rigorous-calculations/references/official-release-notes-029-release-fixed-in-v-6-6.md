# Quantum ESPRESSO release notes — Fixed in v.6.6:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `9a6298913a627fd6d785a5bddfb092c0f967f0f33e432ab9d4fca3b91df3a02a`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in v.6.6:
  * PW: Restart from interrupted calculations  simplified. As a side effect,
    NEB restart now works again
  * Various LIBXC glitches, missing check on metaGGA+USPP/PAW not implemented
  * Fermi energy incorrectly written to xml file in 'bands' calculation
    (did not affect results, just Fermi energy position in band plotting)
    Also: Fermi energy always written to xml file, also for insulators
  * Phonon code in the non-collinear case with magnetization ("domag" case)
    now works properly - courtesy Andrea Urru and Andrea Dal Corso.
  * Incorrect forces, and slightly inconsistent atomic positions, were
    written to xml file for structural optimization and molecular dynamics
    now works properly - courtesy Andrea Urru and Andrea Dal Corso.
    written to xml file, leading to errors in some codes (e.g., thermo_pw)
    using that piece of information (fixed by Alberto Otero de la Roza)
  * PPACF wasn't working with the "lfock" option: wavefunctions were no longer
    read from file because read_file had been replaced by read_file_new
  * Wrong phonons could result in some cases from an incompatibility between
    the FFT grid and the symmetry (typically occurrence: actual symmetry higher
    than the symmetry of the Bravais lattice) - Noticed by Matteo Calandra.
  * Bug in PHonon+U for the symmetrization in the spin-polarized case when 
    the Hubbard channel is "s" (noticed by Jin-Jian Zhou)
 
```
