# Quantum ESPRESSO release notes — Fixed in 5.3.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `fb119fc32cc9df63d68f4c87a07969c6c32a98c34aeab3bcbd4a0538a8ebb858`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.3.0 version:

  * projwfc.x: When pw.x was run on a different number of processors and
    twfcollect was not true, projwfc.x was silently giving wrong results.
    Thanks to Hande Toffoli for reporting.
  * Usage of "~" in pseudo_dir is sometimes acceptable by fortran but not 
    by C. If so, a message is printed instead of weird characters in MD5.
  * PHonon: Gamma-specific code segfaulting with GGA
  * NaN's in stress with nonlocal functionals when the physical dimensions of
    FFT arrays is larger than the true ones and arrays are padded with zeros
  * pw.x: "task-group" parallelization wasn't working properly when the number
    of bands was smaller than the number of task groups. Affects v.5.2.1.
  * TDDFPT: lrpa (Random Phase Approximation) keyword was not present in 
    the namelist for turbo_lanczos.x code. The turboEELS code was not 
    working correctly with just one k point; for metals there were wrong
    weights leading to small errors near the Fermi level; the code was not
    working correctly with ultrasoft PP's. 
  * pw.x: stress with TS-vdw wasn't correct - courtesy of Thomas Markovich
  * The local correlation energy of B3LYP hybrid functional wasn't the "true" 
    one for B3LYP. This caused discrepancies up to of a few tenths of eV 
    in Kohn-Sham energies with respect to the "true" B3LYP. VWN is used
    to define the LDA correlation. B3LYP-V1R (B3LYP using VWN_1_RPA instead) 
    has also been added.
  * Constrained dynamics in pw.x wasn't completely correct
```
