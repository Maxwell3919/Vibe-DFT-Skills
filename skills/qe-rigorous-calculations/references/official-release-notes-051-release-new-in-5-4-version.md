# Quantum ESPRESSO release notes — New in 5.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `798f885c6b54a70799a7ce45ded8f5ba92327b7e50c5c5f9cabbbfb37254b860`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 5.4 version:

  * Calculation of the Magnetic anisotropy energy is implemented (in the limit 
    of small spin-orbit coupling) using the Force theorem (A. Smogunov)
  * Support for FFT with ARM Performance Library (-D__ARM_LIB) added (F. Spiga)
  * Non-blocking FFT communications (-D__NON_BLOCKING_SCATTER) (C. Cavazzoni)
  * Bethe-Salpeter equation added to GWL (P. Umari)
  * Support for QM-MM using MPI (C. Cavazzoni and M. Ippolito)
  * Phonons with vdw-DF (S. de Gironcoli and R. Sabatini) and with DFT-D2
    (P. Giannozzi and F. Masullo) 
  * Addition of EPW to compute electron-phonon properties using Wannier 
    interpolations (S. Poncé, E. R. Margine, C. Verdi, and F. Giustino).
```
