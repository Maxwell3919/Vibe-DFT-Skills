# CP2K official manual snapshot: admm

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html
- Raw SHA-256: 218089ffef6ff1fabac7d76e4a4fd61be6d79262a7889107f5011b771b1220f3
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# AUXILIARY\_DENSITY\_MATRIX\_METHOD

**References:** [Guidon2010](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2010)

Controls the auxiliary density matrix method (ADMM), which evaluates Hartree-Fock exchange on a smaller auxiliary basis and adds an exchange correction. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L686)\]

## Keywords

-   [ADMM\_PURIFICATION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.ADMM_PURIFICATION_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.ADMM_PURIFICATION_METHOD")

-   **[ADMM\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.ADMM_TYPE "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.ADMM_TYPE")**

-   [BLOCK\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.BLOCK_LIST "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.BLOCK_LIST")

-   [EPS\_FILTER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EPS_FILTER "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EPS_FILTER")

-   **[EXCH\_CORRECTION\_FUNC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EXCH_CORRECTION_FUNC "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EXCH_CORRECTION_FUNC")**

-   [EXCH\_SCALING\_MODEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EXCH_SCALING_MODEL "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.EXCH_SCALING_MODEL")

-   [METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.METHOD")

-   [OPTX\_A1](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_A1 "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_A1")

-   [OPTX\_A2](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_A2 "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_A2")

-   [OPTX\_GAMMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html#CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_GAMMA "CP2K_INPUT.FORCE_EVAL.DFT.AUXILIARY_DENSITY_MATRIX_METHOD.OPTX_GAMMA")


## Keyword descriptions

### ADMM\_PURIFICATION\_METHOD*: enum* *\= MO\_DIAG*

**Valid values:**

-   `NONE` Do not apply any purification

-   `CAUCHY` Perform purification via general Cauchy representation

-   `CAUCHY_SUBSPACE` Perform purification via Cauchy representation in occupied subspace

-   `MO_DIAG` Calculate MO derivatives via Cauchy representation by diagonalization

-   `MO_NO_DIAG` Calculate MO derivatives via Cauchy representation by inversion

-   `MCWEENY` Perform original McWeeny purification via matrix multiplications

-   `NONE_DM` Do not apply any purification, works directly with density matrix


Method that shall be used for wavefunction fitting. Use MO\_DIAG for MD. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L711)\]

### ADMM\_TYPE*: enum* *\= NONE*

**Valid values:**

-   `NONE` No short name is used, use specific definitions (default)

-   `ADMM1` ADMM1 method from Guidon2010

-   `ADMM2` ADMM2 method from Guidon2010

-   `ADMMS` ADMMS method from Merlot2014

-   `ADMMP` ADMMP method from Merlot2014

-   `ADMMQ` ADMMQ method from Merlot2014


**References:** [Guidon2010](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2010), [Merlot2014](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#merlot2014)

**Mentions:** ⭐[HFX with ADMM](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/admm.html)

Named ADMM variant from the literature. This shortcut sets METHOD, ADMM\_PURIFICATION\_METHOD, and EXCH\_SCALING\_MODEL consistently for the selected variant. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L693)\]

### BLOCK\_LIST*: integer\[ \]*

**Keyword can be repeated.**

**Usage:** *BLOCK\_LIST {integer} {integer} .. {integer}*

Specifies a list of atoms. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L800)\]

### EPS\_FILTER*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_FILTER*

Define accuracy of DBCSR operations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L807)\]

### EXCH\_CORRECTION\_FUNC*: enum* *\= DEFAULT*

**Valid values:**

-   `DEFAULT` Use PBE-based corrections according to the chosen interaction operator.

-   `PBEX` Use PBEX functional for exchange correction.

-   `NONE` No correction: X(D)-x(d)-> 0.

-   `OPTX` Use OPTX functional for exchange correction.

-   `BECKE88X` Use Becke88X functional for exchange correction.

-   `PBEX_LIBXC` Use PBEX functional (LibXC implementation) for exchange correction.

-   `BECKE88X_LIBXC` Use Becke88X functional (LibXC implementation) for exchange correction.

-   `OPTX_LIBXC` Use OPTX functional (LibXC implementation) for exchange correction.

-   `DEFAULT_LIBXC` Use PBE-based corrections (LibXC where possible) to the chosen interaction operator.

-   `LDA_X_LIBXC` Use Slater X functional (LibXC where possible) for exchange correction.


**Mentions:** ⭐[HFX with ADMM](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/admm.html)

Exchange functional used for the ADMM correction. It should be chosen consistently with the exchange functional in the main XC setup. LibXC implementations require linking with LibXC. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L759)\]

### EXCH\_SCALING\_MODEL*: enum* *\= NONE*

**Valid values:**

-   `NONE` No scaling is enabled, refers to methods ADMM1, ADMM2 or ADMMQ.

-   `MERLOT` Exchange scaling according to Merlot (2014)


Scaling of the exchange correction calculated by the auxiliary density matrix. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L747)\]

### METHOD*: enum* *\= BASIS\_PROJECTION*

**Valid values:**

-   `BASIS_PROJECTION` Construct auxiliary density matrix from auxiliary basis.

-   `BLOCKED_PROJECTION_PURIFY_FULL` Construct auxiliary density from a blocked Fock matrix, but use the original matrix for purification.

-   `BLOCKED_PROJECTION` Construct auxiliary density from a blocked Fock matrix.

-   `CHARGE_CONSTRAINED_PROJECTION` Construct auxiliary density from auxiliary basis enforcing charge constrain.


Method that shall be used for wavefunction fitting. Use BASIS\_PROJECTION for MD. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L730)\]

### OPTX\_A1*: real* *\= 1.05151000E+000*

OPTX a1 coefficient \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L784)\]

### OPTX\_A2*: real* *\= 1.43169000E+000*

OPTX a2 coefficient \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L789)\]

### OPTX\_GAMMA*: real* *\= 6.00000000E-003*

OPTX gamma coefficient \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L794)\]
