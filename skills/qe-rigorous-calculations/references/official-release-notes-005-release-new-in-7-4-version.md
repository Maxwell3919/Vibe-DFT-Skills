# Quantum ESPRESSO release notes — New in 7.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `945f1acbdc7027fd841ca552ff4e6b5afddbaf211849d760cf494be821ae668d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 7.4 version:
  * Added to PW/tools MINpuT: an auxiliary DFT input generation script for
    performing mismatched interface theory (MINT). See E. Gerber et al.,
    Phys. Rev. Lett. 124, 106804 (2020)
  * Linear response phonon calculations with a two-chemical potential approach
    by G. Marini, M. Calandra [Phys. Rev. B 104, 144103(2021)].
  * Enabling detection of symmetries by comparison of species labels for example 
      Hf1 is equivalent with Hf2 , O1 is equivalent to O2 etc 
     (available with control variable symmetries_with_labels) 
      by:  M. Park, R. Masuki 
  * Enabling detection and optional usage of spin flip symmetries, for now excluding the 
    spin translation case ( Identity + fractional translation + spin_flip) 
     by: R. Masuki  
```
