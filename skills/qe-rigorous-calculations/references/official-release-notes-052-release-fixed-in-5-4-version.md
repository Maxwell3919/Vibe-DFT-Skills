# Quantum ESPRESSO release notes — Fixed in 5.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `5b4e4c77f73746d6f03856d5dc793adbac7d4dc1e023b12cab686c452bc3293d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.4 version:

  * New configure wasn't working properly for some Macintosh due to a
    missing line (commit 11976) and on BG (commit 12333)
  * Possible conflict between FFTW in MKL and in Modules/fftw.c solved 
    (commit 11980)
  * Incorrect printout from bands.x for nspin=2 (commit 12064)
  * parallel make broken by missing dependency (commit 12076)
  * generate_vdW_kernel was crashing in parallel on more than 210 processors
    (210 = default number of different q_i and q_j pairs) (commit 12077)
  * Incorrect normalization in epsilon.f90 for nspin=2, some inaccuracy
    for 'mv' and 'mp' smearing (courtesy of Tae Yun Kim and Cheol-Hwan Park,
    Seoul National University) (commit 12082)
  * Incorrect sum over pools in epsilon.f90 for nspin=2 (courtesy of Mariella
    Ippolito, CINECA) (commit 12218)
  * Hybrid functionals with USPP and k-point parallelization now work 
    (commit 12242)
  * Raman with no symmetry wasn't working properly due to bad logic of
    routines symmatrix3 and symtensor3 (courtesy of Marc Blanchard and
    Michele Lazzeri, IMPMC) (commit 12334)
```
