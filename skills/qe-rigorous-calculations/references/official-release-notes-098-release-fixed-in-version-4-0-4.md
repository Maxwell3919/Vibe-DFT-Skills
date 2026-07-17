# Quantum ESPRESSO release notes — Fixed in version 4.0.4:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `9db24bfe7dcf44435e14cdcfea35a4d9d123a9b078b599dc012ca42f81a76a66`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0.4:

  * Structural optimization with external sawtooth potential was not
    working correctly (electric field disappeared after first run).
    All versions after october 2005 affected.
  *  problem in FFTW v.3 driver in parallel execution (Davide)
  *  option maxirr disabled
  *  memory leak in pw_readfile in parallel
  *  the phonon code was not working when wf_collect=.true. and
     either ldisp=.true. or lnscf=.true. 
  *  incorrect make.sys produced by configure on some IBM machines
  *  rigid.f90: the fix introduced in v. 4.0.1 to improve convergence
     wasn't really correct 

                                * * * * *
```
