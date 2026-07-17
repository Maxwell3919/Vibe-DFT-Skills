# Quantum ESPRESSO release notes — Incompatible changes in version 6.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `e072b923248ac6db33294b1eda10cc676bc8192fb461fa1c2e9f3d98a2dc846c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in version 6.4 version:
  * Charge density in the LSDA case is stored as (up+down, up-down) and no longer 
    as (up,down). Output data format is unchanged to (up+down, up-down)
  * Non-symmorphic operations are always allowed and the FFT grid is made
    commensurate. Meaning and usage of input variable "use_all_frac" changed.
  * Old format (-D__OLDXML) deleted. Everything should work as before but some
    exotic options might have problems. The following utilities no longer work:
    - cppp.x (was reading old format only)
    - importexport.x (superseded by hdf5 for portable binaries)
    - bgw2pw.x (was writing old format only)
  * Several routines moved from PHonon/PH to LR_Modules
  * Module "wavefunctions_module" renamed "wavefunctions"
  * TDDFPT: the variables ecutfock, tqr, and real_space are no longer input 
    variables of turbo_lanczos.x and turbo_davidson.x. Instead, they are read 
    from the XML file produced by pw.x. The variable real_space_debug was removed.
```
