# INPUT_kcw — NAMELIST: &SCREEN — Variable: eps_inf

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `3d6429d0f78d9ff40938cb94338de2230c148bb09b6cf3e4eadcc0a835b661e3`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       eps_inf
   
   Type:           REAL
   Default:        1.d0
   Description:    The macroscopic dielectric constant. Needed for the Gygi-Baldereschi
                   scheme if "l_vcut" = .TRUE.
                   Typically from exp or from a ph.x calculation.
                   
                   NOTA BENE: This would be equivalent to a Makov-Payne correction. It works well
                   for cubic systems. Less well for anisotropic systems.
                   
                   ANISOTROPIC SYSTEMS: In this case a generalization of the GB scheme is implemented
                   based on Nano Lett.,9, 975 (2009). It requires the full dielectric tensor to be provided.
                   The code searches (in the working dir) for a file named "eps.dat" containing the macrospocic
                   dielectric tensor. If it does not find it, the value "eps_inf" provided in input will be
                   used (isotropic approximation). If not even "eps_inf" is provided in input no correction
                   is applied to the screened KC correction.
   +--------------------------------------------------------------------
   
```
