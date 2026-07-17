# Quantum ESPRESSO release notes — Fixed in 6.8 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `3b2543b07e795150b47215b2a11bda86d32747a32ee098b1d1625cc744569459`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 6.8 version:
  * Fictitious charge particle (FCP) works again. [arXiv:2012.10090]
  * Bugfix in HP: the hp.x calculation was not stopping smoothly when
    "perturb_only_atom" was used (this bug is not present in earlier 
    versions, i.e. <6.7)
  * Phonon restart was broken in some cases due to bad occupations
    written to xml file
  * ELF with nspin=2 was not correct (noticed by Dong Yang, JSG)
  * "cube" file with data interpolated by B-splines was not correct 
    (fixed by Satomichi Nisihara)
  * Dumb and horrible bug in PAW relativistic calculations (QE 6.7 only):
    a bad tag name was searched for in PP, leading to a small but non
    negligible error. Noticed by Minkyu Park (Univ. of Ulsan, Rep. of Korea).
    Also fixed a "wrong offset" error that could occur in DFT+U for some
    relativistic PP files (found in a report by Ignacio Martin Alliati)
  * Solution to the long-standing problem of non-monotonic N(E) in 
    Methfessel-Paxton and Marzari-Vanderbilt smearing, occasionally resulting 
    in an incorrect choice of the Fermi energy (Flaviano José dos Santos, EPFL).
    Results, in particular for the Fermi energy, may change a little bit, but
    either they are the same or are systematically improved wrt previous ones.
  * There was a missing 2pi/a factor in the case of loto_2d = .true.. Found 
    and explained in M. Royo and M. Stengel, https://arxiv.org/abs/2012.07961.
  * The rho => 0 limit of spin-polarized BEEF XC energy was not correct,
    leading to funny total energy numbers and problems in structural optimization
    (fixed by Gabriel S. Gusmão, Georgia Tech)
  * In some cases the new xml code of v.6.7 wrote UPF files that could not be read
    because they contained too long lines (noticed by Felix Goudreault, U. Montreal)
  * Bug in variable-cell hybrid DFT fixed: it was broken since v.6.5.
  * Small random errors in some XC spin-polarized functionals in OMP execution
  * The new fit introduced in v.6.7 of ev.x wasn't always working as expected
  * alpha2f.x wasn't reading the input any longer in v.6.7
    (noticed by Rico Pratama, Chungbuk Nat.U. Cheongju, Rep. of Korea)
  * turboLanczos with hybrids + (d0psi_rs=.true.) + (ipol/=4) was crashing
  * Restart for DFT+U+V was not working  
  * Restart for "Force theorem" was not working properly and gave wrong results
  * ld1.x may crash while writing UPF files due to unallocated r and rab arrays
    (noticed and fixed by Hitoshi Mori)
```
