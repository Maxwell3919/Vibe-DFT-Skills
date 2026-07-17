# Quantum ESPRESSO release notes — New in 6.4.1 branch :

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b7ccea748ea3d033eed1390d670091c62a6e1384a4eaea37491fe8f03728f883`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.4.1 branch :
  * A warning is issued if the lattice parameter seems to be a conversion
    factor instead of a true lattice parameter. Conversion should be achieved
    with the appropriate options, not with dirty tricks. In the future this
    will no longer be allowed
  * A warning is issued if ibrav=0 is used for systems having symmetry. If not
    properly done this may lead to strange problems with symmetry detection
    and symmetrization. Lattice information should be used if available.

Problems fixed in 6.4.1 branch :
  * Two bugs fixed in HP: 1) the code was not working correctly when fractional
    translations were present, 2) there was a bug in the case when either there
    is only one k point, or when k pools are used and some of the pools have
    only one k point.
  * Restart of ph.x with 2D boundary conditions has been fixed (see gitlab
    issue #102)
  * XML file correctly written if tetrahedra are used (see gitlab issue #103)
```
