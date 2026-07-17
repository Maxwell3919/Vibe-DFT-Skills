# Quantum ESPRESSO release notes — Fixed in version 4.0:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `fe50eded87869dadb96683444e121a92bc8a574c65eeaa46566173d909f012d0`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0:

  * Unpredictable results when the output from a spin-polarized CP
    calculation was used for post-processing. This was due to an
    incorrect treatment of the case where the number of up and down
    states are not the same. There was also an inconsistency in the 
    treatment of the number of up and down electrons, that can be in
    principle real, unlike the number of states that is integer
  * In MD calculations with PWscf, there was the possibility of an
    out-of-bound error, with unpredictable consequences, including 
    in at least one case hanging of parallel jobs
  * Due to a bad dimensioning of variable hubbard_l, DFT+U results could 
    be wrong if atomic type N with U term has N > L=maximum hubbard L
  * a few symmetries were confusing the symmetry finder
  * serious bugs in Berry's phase calculation. It affected only the US 
    case and only some terms, so the error was small but not negligible. 
    There were three different bugs, one introduced when the spherical
    harmonics were modified in the rest of the code, two that I think
    have been there from the beginning.
  * various glitches with wf_collect option in the non-collinear case
  * mix_rho was not working properly for lsda with data saved to file
    and double grid

                                 * * * * *
```
