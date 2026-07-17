# Quantum ESPRESSO release notes — Incompatible changes in 6.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `8d80b83bc76b7859c157ca5e499a0f7f1c2b918e1dffcab8cbb2ac27fa1dd8fa`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.2 version:

  * MAJOR restructuring of the distribution:
    - diagonalizers moved to KS_Solvers/
    - general utility modules moved to UtilXlib/
  * MAJOR restructuring of parallel FFTs, affecting ordering of real-space
    arrays
  * Restructuring of C routines, introduction of ISO_C_BINDING:
    - memstat moved to module wrappers
    - f_wall and f_tcpu, in module mytime, replace previous fortran wrappers 
      for cclock and scnds, respectively. The latter remain as C functions.
    - fft_defs.h and related configure and makedep stuff deleted
  * module pwcom no longer contains modules gvect, gvecs, references to
    some variables in modules constants, cell_base
  * The new XML format with schema is now the default. Use configure option
    "--disable-xml", or add -D__OLDXML to MANUAL_FLAGS in make.inc, to revert
    to the old xml format. IMPORTANT NOTICE: the new format is incompatibile 
    both with the "old" format and with the previous "new" one: files may be
    in different locations with different names and contain different data.
    IMPORTANT NOTICE 2: the "collected" format is now the default
    IMPORTANT NOTICE 3: the new format uses FoX instead of iotk
  * Hybrid functionals: ACE is now the default for scf calculations (it wasn't
    in 6.1 contrary to what previously stated in this file); it is disabled
    for TD-DFPT. See variable "use_ace".
```
