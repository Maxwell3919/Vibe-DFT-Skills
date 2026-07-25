# CP2K official manual snapshot: xc

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html
- Raw SHA-256: 6dd62cbe5e1a2ec40ee81f90c55c2811f005999cea906d3f9b72c4bbba486d47
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# XC

Parameters needed for the calculation of the eXchange and Correlation potential \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1652)\]

Subsections

-   [ADIABATIC\_RESCALING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/ADIABATIC_RESCALING.html)
-   [GCP\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/GCP_POTENTIAL.html)
-   [HF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html)
-   [HFX\_KERNEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HFX_KERNEL.html)
-   [VDW\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL.html)
-   [WF\_CORRELATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html)
-   [XC\_FUNCTIONAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/XC_FUNCTIONAL.html)
-   [XC\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/XC_GRID.html)
-   [XC\_KERNEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/XC_KERNEL.html)
-   [XC\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/XC_POTENTIAL.html)

## Keywords

-   [2ND\_DERIV\_ANALYTICAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.2ND_DERIV_ANALYTICAL "CP2K_INPUT.FORCE_EVAL.DFT.XC.2ND_DERIV_ANALYTICAL")

-   [3RD\_DERIV\_ANALYTICAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.3RD_DERIV_ANALYTICAL "CP2K_INPUT.FORCE_EVAL.DFT.XC.3RD_DERIV_ANALYTICAL")

-   [DENSITY\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.DENSITY_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.XC.DENSITY_CUTOFF")

-   [DENSITY\_SMOOTH\_CUTOFF\_RANGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.DENSITY_SMOOTH_CUTOFF_RANGE "CP2K_INPUT.FORCE_EVAL.DFT.XC.DENSITY_SMOOTH_CUTOFF_RANGE")

-   [GRADIENT\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.GRADIENT_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.XC.GRADIENT_CUTOFF")

-   [NSTEPS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.NSTEPS "CP2K_INPUT.FORCE_EVAL.DFT.XC.NSTEPS")

-   [STEP\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.STEP_SIZE "CP2K_INPUT.FORCE_EVAL.DFT.XC.STEP_SIZE")

-   [TAU\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.TAU_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.XC.TAU_CUTOFF")


## Keyword descriptions

### 2ND\_DERIV\_ANALYTICAL*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *2ND\_DERIV\_ANALYTICAL logical*

Use analytical formulas or finite differences for 2nd derivatives of XC \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1725)\]

### 3RD\_DERIV\_ANALYTICAL*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *3RD\_DERIV\_ANALYTICAL logical*

Use analytical formulas or finite differences for 3rd derivatives of XC \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1732)\]

### DENSITY\_CUTOFF*: real* *\= 1.00000000E-010*

**Usage:** *density\_cutoff 1.e-11*

The cutoff on the density used by the xc calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1658)\]

### DENSITY\_SMOOTH\_CUTOFF\_RANGE*: real* *\= 0.00000000E+000*

**Usage:** *DENSITY\_SMOOTH\_CUTOFF\_RANGE {real}*

Parameter for the smoothing procedure in xc calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1671)\]

### GRADIENT\_CUTOFF*: real* *\= 1.00000000E-010*

**Usage:** *gradient\_cutoff 1.e-11*

The cutoff on the gradient of the density used by the xc calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1664)\]

### NSTEPS*: integer* *\= 3*

**Usage:** *NSTEPS 4*

Number of steps to consider in each direction for the numerical evaluation of XC derivatives. Must be a value from 1 to 4 (Default: 3). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1746)\]

### STEP\_SIZE*: real* *\= 1.00000000E-003*

**Usage:** *STEP\_SIZE 1.0E-3*

Step size in terms of the first order potential for the numerical evaluation of XC derivatives \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1739)\]

### TAU\_CUTOFF*: real* *\= 1.00000000E-010*

**Usage:** *tau\_cutoff 1.e-11*

The cutoff on tau used by the xc calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L1677)\]
