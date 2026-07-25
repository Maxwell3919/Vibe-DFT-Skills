# CP2K official manual snapshot: eigensolvers

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/index.html
- Raw SHA-256: ce26ad20ae8ea928612d7a480f636f7db2f07a63ab860db966c6ec838e6c1c39
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# Eigensolvers

-   [cuSOLVERMp](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/cusolvermp.html)
-   [DLA-Future](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/dlaf.html)
-   [ELPA](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/elpa.html)

CP2K integrates multiple libraries for the solution of eigenvalue problems. ScaLAPACK is a mandatory dependency when using MPI, but GPU-accelerated libraries are optionally available.
