# Quantum ESPRESSO release notes — Fixed in version 2.1.3:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6a086ec6f56c666ec3a2308bfed77b559fc55b3bb10dac6cf8438bc863c1b74e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 2.1.3:
 
  * case ibrav=0 in CP was not properly working
  * forces in CP with core corrections were wrong
    (reported by Giacomo Saielli)
  * damped variable-cell dynamics in PWscf was not working properly
  * lambda.x could yield NaN's on negative frequencies
  * option "write_save" was not working in parallel
  * diagonalization of (0,0) matrix in init_paw_1
  * out-of-bound error in readnewvan.f90 fixed
  * FPMD: bug with UPF PP when betas are not ordered as l=0,1,2,...
  * Possible out-of-bound error with US PP in some cases
  * Martins-Troullier norm-conserving PP generation had a small
    error when rcloc > rcut(l)
  * the default for relativistic vs nonrelativistic calculation
    in the atomic code was the opposite of what was intended
  * electron-phonon calculation was not working properly if called
    after a restart
  * Parallel execution on local filesystems (i.e. not visible to all
    processors) could hang due to a bad check in charge extrapolation
  * When imposing hermiticity in matdyn.x and dynmat.x codes in pwtools
    routine dyndiag was actually computing the complex conjugate of
    the dynamical matrix. Eigenvectors were therefore wrong, while
    eigenvalues were fine. (thanks to Nicolas Mounet)

                                 * * * * *
```
