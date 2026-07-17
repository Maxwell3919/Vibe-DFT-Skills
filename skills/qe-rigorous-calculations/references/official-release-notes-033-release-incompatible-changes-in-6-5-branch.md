# Quantum ESPRESSO release notes — Incompatible changes in 6.5 branch :

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `eb13cccfa3f1d06164bb7804c8527586911d10d4ffb6f43dbad6c8bcb88240ea`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.5 branch :
  * Major changes inside the exchange-correlation code; XC routines moved
    inside modules but no other changes are needed for calling routines
  * ibrav=-13 crystal axis converted to a more standard orientation.
    Atomic positions in crystal axis for the previous convention can
    be converted by applying the transformation (x,y,z) => (y,-x,z)
  * Initialization has been reorganized, so some initialization routines
    do not perform exactly the same operations as before - should have no
    consequences for codes calling "read_file" to start the calculation,
    but codes separately calling initialization routines may be affected
  * fractional translations "ftau" in FFT grid units no longer existing as
    global variables: replaced by "ft", in crystal axis, computed locally
    where needed (in real-space symmetrization only)
```
