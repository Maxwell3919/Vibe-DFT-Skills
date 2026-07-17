# INPUT_CP — NAMELIST: &SYSTEM — Variable: vdw_corr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `e06c7f00fc0758fcb4f294c4047e7f783de6be21a7b028f9a86fdf206b5a7e76`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vdw_corr
   
   Type:           CHARACTER
   Default:        'none'
   Description:    Type of Van der Waals correction. Allowed values:
                   
                      'grimme-d2', 'Grimme-D2', 'DFT-D', 'dft-d': semiempirical Grimme's DFT-D2.
                       Optional variables: "london_s6", "london_rcut"
                       S. Grimme, J. Comp. Chem. 27, 1787 (2006),
                       V. Barone et al., J. Comp. Chem. 30, 934 (2009).
                   
                       'TS', 'ts', 'ts-vdw', 'ts-vdW', 'tkatchenko-scheffler': Tkatchenko-Scheffler
                        dispersion corrections with first-principle derived C6 coefficients
                        Optional variables: "ts_vdw_econv_thr", "ts_vdw_isolated"
                        See A. Tkatchenko and M. Scheffler, Phys. Rev. Lett. 102, 073005 (2009)
                        J. Hermann et al., J. Chem. Phys. 159, 174802 (2023), doi:10.1063/5.0170972
                   
                       'XDM', 'xdm': Exchange-hole dipole-moment model. Optional variables: "xdm_a1", "xdm_a2"
                        (implemented in PW only)
                        A. D. Becke and E. R. Johnson, J. Chem. Phys. 127, 154108 (2007)
                         A. Otero de la Roza, E. R. Johnson, J. Chem. Phys. 136, 174109 (2012)
                   
                   Note that non-local functionals (eg vdw-DF) are NOT specified here but in "input_dft"
   +--------------------------------------------------------------------
   
```
