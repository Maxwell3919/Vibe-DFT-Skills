# Quantum ESPRESSO release notes — Fixed in version 4.0.3:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `e584c4e3b6f7748257625306b6e4fb70d0acb63609f8236ac6a160dc5810b48b`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0.3:

  * CP: array qv allocated in newd wasn't deallocated in all cases,
    leading to either a crash or a memory leak (Ralph)
  * Task groups bug fix: array tg_rho was not cleared at every k point cycle. 
    This was causing problems with some combinations of "-npool" and "-ntg".
  * PWCOND: a bug with some array bounds fixed (A. Smogunov) 
  * Problem with the generation of the atomic wavefunctions in the
    projwfc code when a scalar relativistic PP is used with lspinorb=.true.
  * Bug fix in symmetry analysis for the case S_6 (reported by Marino 
    Vetuschi Zuccolini) and also in: S_4, T_h, C_3h, C_4h, C_6h. 

                                * * * * *
```
