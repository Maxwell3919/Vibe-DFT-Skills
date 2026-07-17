# Quantum ESPRESSO release notes — New in 5.1.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `1bff826f32048fe742d72f05f03df3001ceb7804c372d92ff0ceb1e62be86b48`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 5.1.1 version:

  * CP: Hybrid functionals with Wannier functions
  * Added possibility to provide structure via space-group number and
    Wyckoff positions (experimental)
  * Added vdW-DF-cx, Berland and Hyldgaard, PRB 89, 035412 (2014)
    (courtesy of Timo Thonhauser)
  * PW: TB09 meta-GGA functional (requires libxc)
  * PW: the code can capture "signals". typically sent by batch queues
    when allowed time is close to expire, and terminate gracefully.
    Experimental, to be enabled at compile time (see the user guide)
  * TDDFPT: Implemented a restart option in turbo_Davidson
```
