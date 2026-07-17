# Quantum ESPRESSO release notes — Incompatible changes in version 4.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `7a8ff6a5597ebfdf9ade1c58bdef9a66877b861e2ba1e5222cf0666fc1bba84e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in version 4.2:

  * changed defaults:
    startingwfc='atomic+random' in pw.x (instead of 'atomic')
  * calculations 'fpmd', 'fpmd-neb' removed from CP: use 'cp' or 'neb'
    instead
  * calculation 'metadyn' and related variables removed from PW and CP:
    use the "plumed" plugin for QE to perform metadynamics calculations
  * nelec, nelup, neldw, multiplicity variables removed from input:
    use tot_charge and tot_magnetization instead
  * calculation of empty Kohn-Sham states, and related variables, removed
    from cp.x: use option disk_io='high' in cp.x to save the charge density,
    read the charge density so produced with pw.x, specifying option
    "calculation='nscf'" or "calculation='bands'"
  * "xc_type" input variable in cp.x replaced by "input_dft" (as in pw.x)
  * ortho_para variable removed from input (CP); diagonalization='cg-serial',
    'david-serial', 'david-para', 'david-distpara', removed as well
    Use command-line option "-ndiag N" or "-northo N" to select how
    many processors to use for linar-algebra (orthonormalization or
    subspace diagonalization) parallelization. Note that the default value
    for ndiag/northo has changed as well: 1 if ScaLAPACK is not compiled,
    Nproc/2 if Scalapack is compiled
  * "stm_wfc_matching" removed from pp.x

                               * * * * *
```
