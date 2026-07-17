# Quantum ESPRESSO release notes — Fixed in version 1.1.2 (f90):

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `cefec4f88b083b4aea9bb039dc4d5c1cc63166937d01279572dd37d33d680221`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.1.2 (f90):

  * a check on the number of arguments to command line in parallel
    execution was added - Intel compiler crashes if attempting to
    read a nonexistent argument
  * tmp_dir was incorrectly truncated to 35 characters in
    parallel execution
  * variable "kfac" was not deallocated in stres_knl. A crash in 
    variable-cell MD could result.
  * an inconsistent check between the calling program (gen_us_dj)
    and the routine calculating j_l(r) (sph_bes) could result in 
    error stop when calculating stress or dielectric properties
  * errors at file close in pw.x and phonon.x in some cases
  * tetrahedra work for parallel execution 
    (ltetra is now distributed in bcast_input)
  * fixed some problems in automatic dependencies (Giovanni Cantele)

                                 * * * * *
```
