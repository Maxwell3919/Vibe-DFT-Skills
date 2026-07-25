# CP2K official manual snapshot: hfx-screening

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html
- Raw SHA-256: 40d9c50f2a0f63a43f4b907280f6bc0eaf970c6ad10371d94fecff2dd2140434
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# SCREENING

**References:** [Guidon2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2008), [Guidon2009](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2009)

Controls screening thresholds for Hartree-Fock exchange integrals. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L340)\]

## Keywords

-   [EPS\_SCHWARZ](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.EPS_SCHWARZ "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.EPS_SCHWARZ")

-   [EPS\_SCHWARZ\_FORCES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.EPS_SCHWARZ_FORCES "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.EPS_SCHWARZ_FORCES")

-   [P\_SCREEN\_CORRECTION\_FACTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.P_SCREEN_CORRECTION_FACTOR "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.P_SCREEN_CORRECTION_FACTOR")

-   **[SCREEN\_ON\_INITIAL\_P](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.SCREEN_ON_INITIAL_P "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.SCREEN_ON_INITIAL_P")**

-   [SCREEN\_P\_FORCES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.SCREEN_P_FORCES "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.SCREENING.SCREEN_P_FORCES")


## Keyword descriptions

### EPS\_SCHWARZ*: real* *\= 1.00000000E-010*

**Usage:** *EPS\_SCHWARZ 1.0E-6*

Schwarz inequality threshold for screening near-field electronic repulsion integrals. Tighter values reduce screening error but increase cost. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L347)\]

### EPS\_SCHWARZ\_FORCES*: real* *\= 1.00000000E-006*

**Usage:** *EPS\_SCHWARZ\_FORCES 1.0E-5*

Schwarz threshold used for force-related electronic repulsion integrals. This is approximately the force accuracy and should normally be similar to EPS\_SCF. Default value is 100\*EPS\_SCHWARZ. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L358)\]

### P\_SCREEN\_CORRECTION\_FACTOR*: real* *\= 0.00000000E+000*

**Usage:** *P\_SCREEN\_CORRECTION\_FACTOR 0.0\_dp*

Recalculates integrals on the fly if the actual density matrix is larger by a given factor than the initial one. If the factor is set to 0.0\_dp, this feature is disabled. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L391)\]

### SCREEN\_ON\_INITIAL\_P*: logical* *\= F*

**Usage:** *SCREEN\_ON\_INITIAL\_P TRUE*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Screen on an initial density matrix. For the first MD step this matrix must be provided by a Restart File. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L383)\]

### SCREEN\_P\_FORCES*: logical* *\= T*

**Usage:** *SCREEN\_P\_FORCES TRUE*

Screens the electronic repulsion integrals for the forces using the density matrix. Will be disabled for the response part of forces in MP2/RPA/TDDFT. This results in a significant speedup for large systems, but might require a somewhat tigher EPS\_SCHWARZ\_FORCES. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L370)\]
