# CP2K official manual snapshot: vibrational-analysis

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html
- Raw SHA-256: 74344c15ab1a3e19785a7a5bc86aebd05622fda8412c4bb9b389424c4dcbd442
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# VIBRATIONAL\_ANALYSIS

Section to setup parameters to perform a Normal Modes, vibrational, or phonon analysis. Vibrations are computed using finite differences, which implies a very tight (e.g. 1E-8) threshold is needed for EPS\_SCF to get accurate low frequencies. The analysis assumes a stationary state (minimum or TS), i.e. tight geometry optimization (MAX\_FORCE) is needed as well. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L66)\]

Subsections

-   [MODE\_SELECTIVE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS/MODE_SELECTIVE.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS/PRINT.html)

## Keywords

-   [DX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.DX "CP2K_INPUT.VIBRATIONAL_ANALYSIS.DX")

-   [FULLY\_PERIODIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.FULLY_PERIODIC "CP2K_INPUT.VIBRATIONAL_ANALYSIS.FULLY_PERIODIC")

-   [INTENSITIES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.INTENSITIES "CP2K_INPUT.VIBRATIONAL_ANALYSIS.INTENSITIES")

-   **[NPROC\_REP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.NPROC_REP "CP2K_INPUT.VIBRATIONAL_ANALYSIS.NPROC_REP")**

-   [PROC\_DIST\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.PROC_DIST_TYPE "CP2K_INPUT.VIBRATIONAL_ANALYSIS.PROC_DIST_TYPE")

-   [TC\_PRESSURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.TC_PRESSURE "CP2K_INPUT.VIBRATIONAL_ANALYSIS.TC_PRESSURE")

-   [TC\_TEMPERATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.TC_TEMPERATURE "CP2K_INPUT.VIBRATIONAL_ANALYSIS.TC_TEMPERATURE")

-   [THERMOCHEMISTRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html#CP2K_INPUT.VIBRATIONAL_ANALYSIS.THERMOCHEMISTRY "CP2K_INPUT.VIBRATIONAL_ANALYSIS.THERMOCHEMISTRY")


## Keyword descriptions

### DX*: real* *\= 1.00000000E-002 \[bohr\]*

Specify the increment to be used to construct the HESSIAN with finite difference method \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L75)\]

### FULLY\_PERIODIC*: logical* *\= F*

**Lone keyword:** `T`

Avoids to clean rotations from the Hessian matrix. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L103)\]

### INTENSITIES*: logical* *\= F*

**Lone keyword:** `T`

Calculation of the IR/Raman-Intensities. Calculation of dipoles and/or polarizabilities have to be specified explicitly in DFT/PRINT/MOMENTS and/or PROPERTIES/LINRES/POLAR \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L109)\]

### NPROC\_REP*: integer* *\= 1*

**Mentions:** ⭐[Simulating Vibronic Effects in Optical Spectra](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/vibronicspec.html)

Specify the number of processors to be used per replica environment (for parallel runs). In case of mode selective calculations more than one replica will start a block Davidson algorithm to track more than only one frequency \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L82)\]

### PROC\_DIST\_TYPE*: enum* *\= BLOCKED*

**Usage:** *PROC\_DIST\_TYPE (INTERLEAVED|BLOCKED)*

**Valid values:**

-   `INTERLEAVED` Interleaved distribution

-   `BLOCKED` Blocked distribution


Specify the topology of the mapping of processors into replicas. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L91)\]

### TC\_PRESSURE*: real* *\= 1.01325000E+005 \[Pa\]*

Pressure for the calculation of the thermochemical data \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L135)\]

### TC\_TEMPERATURE*: real* *\= 2.73150000E+002 \[K\]*

**Usage:** *tc\_temperature 325.0*

Temperature for the calculation of the thermochemical data \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L128)\]

### THERMOCHEMISTRY*: logical* *\= F*

**Lone keyword:** `T`

Calculation of the thermochemical data. Valid for molecules in the gas phase, not supporting phonon frequencies at general **q**\-points beyond wave vector **q** at gamma point. Based on the rigid-rotor harmonic oscillator (RRHO) model, which is known to break down if very low vibrational frequencies are present in a flexible system. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_vib.F#L118)\]
