# INPUT_PW — NAMELIST: &CONTROL — Variable: etot_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `a0acedb936e12016ba1806c2194773ec6cf92988dcff302c0e21dfc562ffaff2`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       etot_conv_thr
   
   Type:           REAL
   Default:        1.0D-4
   Description:    Convergence threshold on total energy (a.u) for ionic
                   minimization: the convergence criterion is satisfied
                   when the total energy changes less than "etot_conv_thr"
                   between two consecutive scf steps. Note that "etot_conv_thr"
                   is extensive, like the total energy.
                   See also "forc_conv_thr" - both criteria must be satisfied
   +--------------------------------------------------------------------
   
```
