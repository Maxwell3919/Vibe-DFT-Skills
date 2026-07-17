# Quantum ESPRESSO release notes — Incompatible changes in 6.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6ac7d8f53a793cffffd322582c9b87790b2b268bedc38a3d57501bf03f8f7ce4`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.0 version:

  * Support for AIX removed
  * The hamiltonian h_psi no longer needs "npw" and "igk" to be initialized
    via module "wvfct", but it needs "current_k" to be set to the index of
    the current k-point
  * k-point dependent variables npw, igk, and (in LR codes) npwq, igkq, 
    become local and point to global variables "ngk" and "igk_k", via the
    k-point index "ik" or, in LR codes, via "ikks" and "ikkq" indices.
    The global variables are computed once, stored in memory, no I/O is done.
    Variable "iunigk" deleted (contained unit for I/O of indices).
  * "nbnd_occ" variable is now dynamically allocated
  * Duplicated and confusing "outdir" variable removed from "io_files"
  * Due to frequent problems with mailers, "make.sys" is renamed "make.inc"
  * "allocate_fft" no longer calls "data_structure" to compute dimensions
    of the various grids: it just allocates FFT arrays
  * QE-GPU plugin not compatible with 6.x (new version is WIP)
  * Configure options "--with-internal-lapack" & "--with-internal-blas" have
    been replaced by a single "--with-netlib". Netlib LAPACK is self-compiled 
    (and also Netlib BLAS which is packaged with it).

                               * * * * *
```
