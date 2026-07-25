# CP2K official manual snapshot: scf-diagonalization

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html
- Raw SHA-256: ce2e520745231e2561e831a52100cad1798e40f0e20de00a40db1cdf7cf204b4
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# DIAGONALIZATION

Set up type and parameters for Kohn-Sham matrix diagonalization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L947)\]

Subsections

-   [DAVIDSON](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION/DAVIDSON.html)
-   [DIAG\_SUB\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION/DIAG_SUB_SCF.html)
-   [FILTER\_MATRIX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION/FILTER_MATRIX.html)
-   [KRYLOV](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION/KRYLOV.html)
-   [OT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION/OT.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.SECTION_PARAMETERS")

-   [ALGORITHM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.ALGORITHM "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.ALGORITHM")

-   [EPS\_ADAPT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_ADAPT "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_ADAPT")

-   [EPS\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_ITER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_ITER")

-   [EPS\_JACOBI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_JACOBI "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.EPS_JACOBI")

-   [JACOBI\_THRESHOLD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.JACOBI_THRESHOLD "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.JACOBI_THRESHOLD")

-   [MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.MAX_ITER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.DIAGONALIZATION.MAX_ITER")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&DIAGONALIZATION T*

controls the activation of the diagonalization method \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L953)\]

### ALGORITHM*: enum* *\= STANDARD*

**Usage:** *ALGORITHM STANDARD*

**Valid values:**

-   `STANDARD` Standard diagonalization: LAPACK methods or Jacobi.

-   `OT` Iterative diagonalization using OT method

-   `LANCZOS` Block Krylov-space approach to self-consistent diagonalisation

-   `DAVIDSON` Preconditioned blocked Davidson

-   `FILTER_MATRIX` Filter matrix diagonalization


Algorithm to be used for diagonalization \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L961)\]

### EPS\_ADAPT*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_ADAPT 0.01*

Required accuracy in iterative diagonalization as compared to current SCF convergence \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L998)\]

### EPS\_ITER*: real* *\= 1.00000000E-008*

**Usage:** *EPS\_ITER 1.e-8*

Required accuracy in iterative diagonalization \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1012)\]

### EPS\_JACOBI*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_JACOBI 1.0E-5*

**References:** [Stewart1982](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stewart1982)

Below this threshold value for the SCF convergence the pseudo-diagonalization method using Jacobi rotations is activated. This method is much faster than a real diagonalization and it is even speeding up while achieving full convergence. However, it needs a pre-converged wavefunction obtained by at least one real diagonalization which is further optimized while keeping the original eigenvalue spectrum. The MO eigenvalues are NOT updated. The method might be useful to speed up calculations for large systems e.g. using a semi-empirical method. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L984)\]

### JACOBI\_THRESHOLD*: real* *\= 1.00000000E-007*

**Usage:** *JACOBI\_THRESHOLD 1.0E-6*

**References:** [Stewart1982](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stewart1982)

Controls the accuracy of the pseudo-diagonalization method using Jacobi rotations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L976)\]

### MAX\_ITER*: integer* *\= 2*

**Usage:** *MAX\_ITER 20*

Maximum number of iterations in iterative diagonalization \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1005)\]
