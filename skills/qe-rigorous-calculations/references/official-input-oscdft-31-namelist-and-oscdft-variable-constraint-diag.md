# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: constraint_diag

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `97acac2f7e5193d26235fc4a4a4bd562a44e6d3522db210325ed116f64cc9eb6`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       constraint_diag
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE., TARGET_OCCUPATION_NUMBERS must contain the
                   eigenvalues of the occupation matrix instead of the full
                   (generally) nondiagonal target occupation matrix.
                   The code will read these eigenvalues and reconstruct the
                   nondiagonal target occupation matrix that will be used
                   for constrained calculations. This should behave similarly
                   to the starting_ns_eigenvalue keyword, but better since the
                   constraint is applied until the constraint_conv_thr is
                   reached (contrary to a simple reinitialization of starting
                   occupations that is done using starting_ns_eigenvalue).
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
