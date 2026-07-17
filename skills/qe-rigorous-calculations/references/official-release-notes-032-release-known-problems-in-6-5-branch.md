# Quantum ESPRESSO release notes — Known problems in 6.5 branch:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `a327886349f0535e9c7f8fa108a1d399275cda7fa28d5626a728ecc312242147`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Known problems in 6.5 branch:
  * The phonon code in the non-collinear case with the "domag" option does 
    not work properly: there is a problem with time reversal symmmetry.
    Such calculation is currently disabled until a fix is found.

Problems fixed in 6.5 branch :
  * at2celldm wasn't properly converting vectors into celldm parameters
    in the ibrav=91 case (Tone)
  * PP: plot_num=1 wasn't working any longer as expected due to forgotten 
    local potential term (noticed by Manoar Hossain, NISER)
  * DOS calculation wasn't honoring "bz_sum='smearing'" if the nscf 
    calculation was performed with tetrahedra, contrary to what stated
    in the documentation (noticed by Mohammedreza Hosseini, Modares Univ.)
  * Time reversal symmetry in tetrahedron routine incorrectly detected
    after a restart in phonon (reported by T. Tadano)
  * pp.x with plot_num=11 in spin-polarized case was issuing a segmentation
    fault error (noticed by Mauricio Chagas da Silva)
  * pp.x with plot_num=17 in spin-polarized case was issuing a bogus 
    error (noticed by Shoaib Muhammad, Sungkyunkwan U.)
  * vc-relax with cell_dofree='z' wasn't working exactly as expected
    (noticed by Daniel Marchand, fixed by Lorenzo Paulatto)
  * Incorrect link to wannier90 package (thanks to Nikolas Garofil)
  * Bug in spin-polarized meta-GGA (noticed by Shoaib Muhammad, 
    Sungkyunkwan U.)
  * Unphysical fractional translations (tau/n with n/=2,3,4,6) were not 
    explicitly discarded, thus leading in unfortunate cases to strange
    values for FFT factors and grids. Also: if "nosym" is true, inversion
    symmetry flag (invsym) and info on FFT factors (fft_fact) must also
    be reset (problem spotted by Thomas Brumme, Leipzig)
  * PPACF wasn't working any longer in v.6.4 and 6.4.1 for nspin=2 and
    for hybrid functionals (fixed by Yang Jiao, Chalmers)
  * option "write_unkg" of pw2wannier90.f90 wasn't working as expected
  * Input parameters (for restarting DFPT+U calculations) read_dns_bare 
    and d2ns_type were missing in the PH input namelist, and moreover
    they were not broadcasted.
  * Option rescale-T and reduce-T now update the target temperature based on
    the previous target temperature, not based on instantaneous temperature
    as before.
  * cppp.x works again
```
