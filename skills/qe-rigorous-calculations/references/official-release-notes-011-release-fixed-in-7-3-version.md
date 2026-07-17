# Quantum ESPRESSO release notes — Fixed in 7.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `74221f552097fb0f0d91a76f616968cafeae8a1957e0ecb4dc95892cbf071a28`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.3 version:
  * Incorrect PP_SEMILOCAL field written for old-style pseudopotentials.
    May cause crashes (but not bad numbers). Reported by Jibiao Li.
  * Wrong output from Libxc-based gga-exchange functionals (gga_x) due to
    a bad multiplicative factor (v7.2 only, noticed by Peter Kraus).
    The exchange+correlation ones (gga_xc) were not affected.
  * The seed for random numbers was not set after the first run. As a result,
    all subsequent runs used the same sequence of random numbers. Affects only
    thermostats in Verlet dynamics for pw.x. Noticed by Han Hsu, NCU Taiwan.
```
