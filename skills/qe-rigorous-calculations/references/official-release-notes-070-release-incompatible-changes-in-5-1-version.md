# Quantum ESPRESSO release notes — Incompatible changes in 5.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `5b6854f267b9013428a7865e13c87282291a595bfb13241bc02628f1224b82ec`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.1 version:

  * Initialization of MPI modified in order to simplify usage of QE routines
    from external codes. It is now possible to run an instance of QE into a
    mpi communicator passed by the external routine. Changes affect a few MPI
    initialization routines (e.g. mp_start) and some MPI related modules;
    the communicator must be explicitly specified when calling mp_* interfaces
    to low-level MPI libraries.
  * Input variable "london" should be replaced by " vdw_corr='Grimme-D2' "
  * Routine "electrons" doesn't deal any longer with non-scf cases;
    use routine "non_scf" instead. For hybrid functionals, the loops over
    the charge density and over the exchange potential have been separated.
  * Restart mechanism of pw.x changed a lot. It works ONLY if you stop
    the code cleanly with the prefix.EXIT file, or by setting "max_seconds";
    disk_io='high' no longer needed (use it ONLY if tight with memory)
    Restarting from hard crashes is no longer supported.
  * Major restructuring of DFT+U and related modules in PW: related variables
    moved to module ldaU, "swfcatom" moved to module "basis"
  * Definition of "nwordwfc" in PP/ follows the same logic as in PW/
  * Calls to "find_equiv_sites" and "writemodes" changed (fixed dimension
    "nax" removed)
  * Call to "open_buffer" changed: unit must be a valid fortran unit > 0;
    max number of records is no longer specified; a new flag explicitly
    specifies if writing to RAM buffer is required. Functionalities of 
    Modules/buffers.f90 have been considerably modified and extended.
```
