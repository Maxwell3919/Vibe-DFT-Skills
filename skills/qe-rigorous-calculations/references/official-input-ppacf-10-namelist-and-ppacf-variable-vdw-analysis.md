# INPUT_PPACF — NAMELIST: &PPACF — Variable: vdW_analysis

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPACF.txt
- Retrieved: 2026-07-17T11:49:41+00:00
- Official source SHA-256: `ec18cfa677f3d5684e7176a867c5d56868b44758bd2d43678d4ee813e1ecfc39`
- Extracted text SHA-256: `d8024bc0924145a1143691e38d814a981778d1ed173dd58ab8868bfb3f15d1bf`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vdW_analysis
   
   Type:           INTEGER
   Description:    Select type of vdw kernel table used in ppacf coupling-constant scaling
                   analysis of nonlocal-correlations in vdW-DF versions:
                   - vdW_analysis = 0: Full Ecnl kenel of vdW-DF method
                   - vdW_analysis = 1: The cumulant- or susceptibility-Ecnl kernel component
                   - vdW_analysis = 2: The pure-vdW-Ecnl kernel component
                   See IOP JCPM (2020) for presentation of the latter two (non-default) options
   Default:        o
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:28:59 CEST 2025
```
