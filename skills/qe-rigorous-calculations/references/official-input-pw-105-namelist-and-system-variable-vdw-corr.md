# INPUT_PW — NAMELIST: &SYSTEM — Variable: vdw_corr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ff0611fa783dc8d85d1105e4060ca5737b849435f9ddcf670a8538327f839624`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vdw_corr
   
   Type:           CHARACTER
   Default:        'none'
   See:            london_s6, london_rcut, london_c6, london_rvdw,
                   dftd3_version, dftd3_threebody, ts_vdw_econv_thr, ts_vdw_isolated, xdm_a1, xdm_a2
   Description:   
                   Type of the van der Waals correction. Allowed values:
    
                   'grimme-d2', 'Grimme-D2', 'DFT-D', 'dft-d' :
                        Semiempirical Grimme's DFT-D2. Optional variables:
                        "london_s6", "london_rcut", "london_c6", "london_rvdw"
                        S. Grimme, J. Comp. Chem. 27, 1787 (2006), doi:10.1002/jcc.20495
                        V. Barone et al., J. Comp. Chem. 30, 934 (2009), doi:10.1002/jcc.21112
    
                   'grimme-d3', 'Grimme-D3', 'DFT-D3', 'dft-d3'  :
                        Semiempirical Grimme's DFT-D3. Optional variables:
                        "dftd3_version", "dftd3_threebody"
                        S. Grimme et al, J. Chem. Phys 132, 154104 (2010), doi:10.1063/1.3382344
    
                   'TS', 'ts', 'ts-vdw', 'ts-vdW', 'tkatchenko-scheffler' :
                        Tkatchenko-Scheffler dispersion corrections with first-principle derived
                        C6 coefficients.
                        Optional variables: "ts_vdw_econv_thr", "ts_vdw_isolated"
                        See A. Tkatchenko and M. Scheffler, PRL 102, 073005 (2009).
                        J. Hermann et al., J. Chem. Phys. 159, 174802 (2023), doi:10.1063/5.0170972
    
                   'MBD', 'mbd', 'many-body-dispersion', 'mbd_vdw' :
                        Many-body dipersion (MBD) correction to long-range interactions.
                        Optional variables: "ts_vdw_isolated"
                        A. Ambrosetti et al., J. Chem. Phys. 140, 18A508 (2014), doi:10.1063/1.4865104
                        J. Hermann et al., J. Chem. Phys. 159, 174802 (2023), doi:10.1063/5.0170972
    
                   'XDM', 'xdm' :
                        Exchange-hole dipole-moment model. Optional variables: "xdm_a1", "xdm_a2"
                        A. D. Becke et al., J. Chem. Phys. 127, 154108 (2007), doi:10.1063/1.2795701
                        A. Otero de la Roza et al., J. Chem. Phys. 136, 174109 (2012),
                        doi:10.1063/1.4705760
    
                   Note that non-local functionals (eg vdw-DF) are NOT specified here but in "input_dft"
   +--------------------------------------------------------------------
   
```
