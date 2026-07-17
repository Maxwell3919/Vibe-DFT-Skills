# Quantum ESPRESSO release notes — Fixed in version 1.0.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `2b29aa3b9510d7d1db959962989842d73803d72dacbf2ed1d5d38d6b3f3eaf2a`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.0.1:

  * recovering from a previous run in pw.x did not work on PC's
  * recovering from a previous run in pw.x did not work for stress
    calculation
  * poolrecover did not compile on some machines (thanks to Eric Wu)
  * PC with absoft compiler (and maybe other cases as well):
    bad type conversions for REAL and CMPLX resulted in poor
    convergence in some test cases. DCMPLX, DREAL used instead.
  * Asymptotic high- and low-density formulae used in PW91 and PBE
    unpolarized functionals gave a small but not negligible error,
    leading to bad convergence of structural optimization
```
