# Quantum ESPRESSO release notes — Fixed in 4.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b37efca8afa7d01b99a5305541c01b0d4968eb506bbbfc106617bffd5187d368`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 4.3 version:

  * CP: Input external pressure is in KBar and not in GPa like it was
    formerly in CP. Input value for variable "press" in cell namelist
    should be given in KBar as stated in the documentation!
  * CP: incorrect stress calculated in the spin-polarized case 
  * CP: memory leak in LDA+U calculations
  * CPPP: spurious line in all versions since 4.2 was causing an error
  * PW: LSDA + Gamma tricks + task groups = not working.
        Also: pw.x -ntg 1 was activating task groups (harmless)
  * PW: corrected an old bug for Berry's phase finite electric field 
        calculations with non-orthorhombic simulation cells. Also fixed 
        an old but minor bug on averaging of Berry phases between strings
  * PW: problem with symmetrization in the non-collinear case
  * PW: tetrahedra+non-collinear case fixed (courtesy of Yurii Timrov)
  * option -D__USE_3D_FFT wasn't working any longer in v.4.2.x
  * PP: calculation of ILDOS with USPP wasn't working in v.4.2.x
  * PH: elph=.true. and trans=.false. was not working any longer. 
  * PH: electron-phonon data file for q2r.x was not properly written in
        some cases (-q not in the star of q). Also: questionable syntax
        for formats in lambda.f90 was not accepted by gfortran
  * D3: k-point parallelization fixed again

                               * * * * *
```
