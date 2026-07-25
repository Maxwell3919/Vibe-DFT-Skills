# CP2K official manual snapshot: sccs

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html
- Raw SHA-256: 44d4e91caee4e40ab46396d57544f0a25f80c9e75232da73f17191a55ccf5c6b
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# SCCS

**References:** [Fattebert2002](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#fattebert2002), [Andreussi2012](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#andreussi2012), [Yin2017](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#yin2017)

Define the parameters for self-consistent continuum solvation (SCCS) model \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2190)\]

Subsections

-   [ANDREUSSI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS/ANDREUSSI.html)
-   [FATTEBERT-GYGI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS/FATTEBERT-GYGI.html)
-   [SAA\_ANDREUSSI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS/SAA_ANDREUSSI.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.SECTION_PARAMETERS")

-   [ALPHA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.ALPHA "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.ALPHA")

-   [BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.BETA "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.BETA")

-   [DELTA\_RHO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.DELTA_RHO "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.DELTA_RHO")

-   [DERIVATIVE\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.DERIVATIVE_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.DERIVATIVE_METHOD")

-   [EPS\_SCCS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.EPS_SCCS "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.EPS_SCCS")

-   [EPS\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.EPS_SCF "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.EPS_SCF")

-   [GAMMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.GAMMA "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.GAMMA")

-   [MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.MAX_ITER "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.MAX_ITER")

-   [METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.METHOD")

-   [MIXING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.MIXING "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.MIXING")

-   [RELATIVE\_PERMITTIVITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html#CP2K_INPUT.FORCE_EVAL.DFT.SCCS.RELATIVE_PERMITTIVITY "CP2K_INPUT.FORCE_EVAL.DFT.SCCS.RELATIVE_PERMITTIVITY")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&SCCS ON*

Controls the activation of the SCCS section \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2200)\]

### ALPHA*: real* *\= 0.00000000E+000 \[mN\*m^-1\]*

Solvent specific tunable parameter for the calculation of the repulsion term \(G^\text{rep} = \alpha S\) where \(S\) is the (quantum) surface of the cavity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2209)\]

### BETA*: real* *\= 0.00000000E+000 \[GPa\]*

Solvent specific tunable parameter for the calculation of the dispersion term \(G^\text{dis} = \beta V\) where \(V\) is the (quantum) volume of the cavity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2222)\]

### DELTA\_RHO*: real* *\= 2.00000000E-005*

Numerical increment for the calculation of the (quantum) surface of the solute cavity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2235)\]

### DERIVATIVE\_METHOD*: enum* *\= FFT*

**Usage:** *DERIVATIVE\_METHOD cd5*

**Valid values:**

-   `FFT` Fast Fourier transformation

-   `CD3` 3-point stencil central differences

-   `CD5` 5-point stencil central differences

-   `CD7` 7-point stencil central differences


Method for the calculation of the numerical derivatives on the real-space grids \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2246)\]

### EPS\_SCCS*: real* *\= 1.00000000E-006*

**Aliases:** EPS\_ITER ,TAU\_POL

**Usage:** *EPS\_ITER 1.0E-7*

Tolerance for the convergence of the polarisation density, i.e. requested accuracy for the SCCS iteration cycle \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2277)\]

### EPS\_SCF*: real* *\= 5.00000000E-001*

**Usage:** *EPS\_SCF 1.0E-2*

The SCCS iteration cycle is activated only if the SCF iteration cycle is converged to this threshold value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2290)\]

### GAMMA*: real* *\= 0.00000000E+000 \[mN\*m^-1\]*

**Aliases:** SURFACE\_TENSION

Surface tension of the solvent used for the calculation of the cavitation term \(G^\text{cav} = \gamma S\) where \(S\) is the (quantum) surface of the cavity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2302)\]

### MAX\_ITER*: integer* *\= 100*

**Usage:** *MAX\_ITER 50*

Maximum number of SCCS iteration steps performed to converge within the given tolerance \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2316)\]

### METHOD*: enum* *\= ANDREUSSI*

**Usage:** *METHOD Fattebert-Gygi*

**Valid values:**

-   `ANDREUSSI` Smoothing function proposed by Andreussi et al.

-   `FATTEBERT-GYGI` Smoothing function proposed by Fattebert and Gygi

-   `SAA_ANDREUSSI` Smoothing function of the solvent aware algorithm


Method used for the smoothing of the dielectric function \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2328)\]

### MIXING*: real* *\= 6.00000000E-001*

**Aliases:** ETA

**Usage:** *MIXING 0.2*

Mixing parameter (Hartree damping) employed during the iteration procedure \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2341)\]

### RELATIVE\_PERMITTIVITY*: real* *\= 8.00000000E+001*

**Aliases:** DIELECTRIC\_CONSTANT ,EPSILON\_RELATIVE ,EPSILON\_SOLVENT

**Usage:** *RELATIVE\_PERMITTIVITY 78.36*

Relative permittivity (dielectric constant) of the solvent (medium) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L2265)\]
