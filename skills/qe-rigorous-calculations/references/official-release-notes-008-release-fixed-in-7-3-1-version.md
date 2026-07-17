# Quantum ESPRESSO release notes — Fixed in 7.3.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6fc19ee4dabcad6e8812f69589258eda7193ab74d2f1f2446e71a0d5ac5f952d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.3.1 version:
  * In CPV the mgga contribution to the force was missing on the GPU side.
    Now it has been added (CPU and GPU runs match).
  * f channel of GTH pseudopotentials fixed again (see issue #86 on gitlab)
    Thanks to Chang Liu for reporting.
  * Distributed parallel diagonalization (option -nd N with N=4,9,16,25,...) 
    crashed when used together with NVidia GPUs (thanks to Laura Bellentani)
  * Old PPs with zero nonlocal part were crashing in parallel execution
    (see issue #633 on gitlab). Affects v.7.3. Thanks to Ye Luo for reporting 
  * assume_isolated='2D' was giving wrong results when used with Gamma tricks
    (see issue #11 on gitlab). Affects all previous versions.
  * assume_isolated='esm' was giving bad forces when used with Gamma tricks.
    Affects v.7.2 and 7.3. Thanks to Giuseppe Mattioli for reporting.
  * Bad atomic symbols in some files used for plotting data (see issue #645
    on gitlab). Affects v.7.3. Thanks to Francesco Filippone for reporting.
  * Since v.6.2, assume_isolated='mt' was yielding bad phonon frequencies 
    (see issue #657). Thanks to Jeremy Rabone for reporting.
```
