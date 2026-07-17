# Quantum ESPRESSO release notes — Fixed in 7.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `cbcf8d7a2e4cd09df62295af16ea00447441d4948a44fd55118c83f51eacedcd`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.0 version:
  * Possible out-of-bound error (gfortran only) could crash DFT+U
  * incorrect exx factor multiplication in the gga term of polarized cx0 
    functional (v.6.8 only)
  * Some build problems occurring under special circumstances
  * Some PP files were not correctly read since v.6.7
  * DFT-D3 with dftd3_version=4 or 6 could produce NaN's in parallel runs
    due to missing zero initialization of some work arrays
  * Ensemble-DFT in CP ("cg") wasn't working any longer for norm-conserving PPs
  * In DFT+U (lda_plus_u_kind = 0 and 1) the pw.x code was printing the squared 
    eigenvectors instead of simply eigenvectors. Now it prints the
    eigenvectors (consistent with lda_plus_u_kind = 2).
  * plotband.x wasn't correctly plotting the bands, under some not-so-special
    circumstances
  * CP with DFT+U could crash when writing the xml file (since v.6.6)
  * Restart of electron-phonon calculations was not working due to a missing
    tag (thanks to Miguel Marques for reporting this)
  * atomic: the exchange of two lines in import_upf.f90 had broken PAW tests
    since v.6.5 (thanks to Chiara Biz for reporting, to AdC for fixing)
  * Calculation of ELF for spin-unpolarized cases was grossly wrong in v.6.8
  * Changes to the i-Pi interface to adapt it to usage with ASE had broken 
    the original functionality
```
