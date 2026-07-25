# CP2K official manual snapshot: scf

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html
- Raw SHA-256: f7bfeb7d25276eb167788547f679bd593f78352b744bd59fe351999367349ad6
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# SCF

Parameters needed to perform an SCF run. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L89)\]

Subsections

-   [DIAGONALIZATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html)
-   [GCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/GCE.html)
-   [MIXING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html)
-   [MOM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MOM.html)
-   [OT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html)
-   [OUTER\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/PRINT.html)
-   [SMEAR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html)

## Keywords

-   **[ADDED\_MOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.ADDED_MOS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.ADDED_MOS")**

-   [CHOLESKY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.CHOLESKY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.CHOLESKY")

-   [EPS\_DIIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_DIIS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_DIIS")

-   [EPS\_EIGVAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_EIGVAL "CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_EIGVAL")

-   [EPS\_LUMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_LUMO "CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_LUMO")

-   **[EPS\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_SCF "CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_SCF")**

-   [EPS\_SCF\_HISTORY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_SCF_HISTORY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.EPS_SCF_HISTORY")

-   [FORCE\_SCF\_CALCULATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.FORCE_SCF_CALCULATION "CP2K_INPUT.FORCE_EVAL.DFT.SCF.FORCE_SCF_CALCULATION")

-   **[IGNORE\_CONVERGENCE\_FAILURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.IGNORE_CONVERGENCE_FAILURE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.IGNORE_CONVERGENCE_FAILURE")**

-   [LEVEL\_SHIFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.LEVEL_SHIFT "CP2K_INPUT.FORCE_EVAL.DFT.SCF.LEVEL_SHIFT")

-   [MAX\_DIIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_DIIS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_DIIS")

-   [MAX\_ITER\_LUMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_ITER_LUMO "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_ITER_LUMO")

-   **[MAX\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_SCF "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_SCF")**

-   [MAX\_SCF\_HISTORY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_SCF_HISTORY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MAX_SCF_HISTORY")

-   [NCOL\_BLOCK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.NCOL_BLOCK "CP2K_INPUT.FORCE_EVAL.DFT.SCF.NCOL_BLOCK")

-   [NROW\_BLOCK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.NROW_BLOCK "CP2K_INPUT.FORCE_EVAL.DFT.SCF.NROW_BLOCK")

-   [ROKS\_F](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_F "CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_F")

-   [ROKS\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_PARAMETERS")

-   [ROKS\_SCHEME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_SCHEME "CP2K_INPUT.FORCE_EVAL.DFT.SCF.ROKS_SCHEME")

-   **[SCF\_GUESS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SCF_GUESS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SCF_GUESS")**


## Keyword descriptions

### ADDED\_MOS*: integer\[ \]* *\= 0*

**Usage:** *ADDED\_MOS*

**Mentions:** ⭐[Density of States](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/dos.html), ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

Number of additional molecular orbitals added for each spin channel. This is commonly needed for smearing, excited-state, or post-Hartree-Fock calculations. Use -1 to add all available orbitals. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L238)\]

### CHOLESKY*: enum* *\= RESTORE*

**Usage:** *CHOLESKY REDUCE*

**Valid values:**

-   `OFF` The cholesky algorithm is not used

-   `REDUCE` Reduce is called

-   `RESTORE` Reduce is replaced by two restore

-   `INVERSE` Restore uses operator multiply by inverse of the triangular matrix

-   `INVERSE_DBCSR` Like inverse, but matrix stored as dbcsr, sparce matrix algebra used when possible


If the cholesky method should be used for computing the inverse of S, and in this case calling which Lapack routines \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L180)\]

### EPS\_DIIS*: real* *\= 1.00000000E-001*

**Usage:** *EPS\_DIIS 5.0e-2*

Threshold on the convergence to start using DIAG/DIIS or OT/DIIS. Default for OT/DIIS is never to switch. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L199)\]

### EPS\_EIGVAL*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_EIGVAL 1.0*

Throw away linear combinations of basis functions with a small eigenvalue in S \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L193)\]

### EPS\_LUMO*: real* *\= 1.00000000E-005*

**Aliases:** EPS\_LUMOS

**Usage:** *EPS\_LUMO 1.0E-6*

Target accuracy for the calculation of the LUMO energies with the OT eigensolver. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L133)\]

### EPS\_SCF*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_SCF 1.e-6*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html), ⭐[Monte Carlo](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/monte_carlo.html)

Target convergence threshold for the inner SCF cycle. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L168)\]

### EPS\_SCF\_HISTORY*: real* *\= 0.00000000E+000*

**Aliases:** EPS\_SCF\_HIST

**Lone keyword:** `1.00000000E-005`

**Usage:** *EPS\_SCF\_HISTORY 1.e-5*

Target accuracy for the SCF convergence after the history pipeline is filled. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L174)\]

### FORCE\_SCF\_CALCULATION*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *FORCE\_SCF\_CALCULATION logical\_value*

Request a SCF type solution even for nonSCF methods. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L296)\]

### IGNORE\_CONVERGENCE\_FAILURE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *IGNORE\_CONVERGENCE\_FAILURE logical\_value*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

If true, only a warning is issued if an SCF iteration has not converged. By default, a run is aborted if the required convergence criteria have not been achieved. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L286)\]

### LEVEL\_SHIFT*: real* *\= 0.00000000E+000 \[hartree\]*

**Aliases:** LSHIFT

**Usage:** *LEVEL\_SHIFT 0.1*

Use level shifting to improve convergence \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L159)\]

### MAX\_DIIS*: integer* *\= 4*

**Aliases:** MAX\_DIIS\_BUFFER\_SIZE

**Usage:** *MAX\_DIIS 3*

Maximum number of DIIS vectors to be used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L152)\]

### MAX\_ITER\_LUMO*: integer* *\= 299*

**Aliases:** MAX\_ITER\_LUMOS

**Usage:** *MAX\_ITER\_LUMO 100*

Maximum number of iterations for the calculation of the LUMO energies with the OT eigensolver. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L125)\]

### MAX\_SCF*: integer* *\= 50*

**Usage:** *MAX\_SCF 200*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Monte Carlo](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/monte_carlo.html)

Maximum number of inner SCF iterations for one electronic optimization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L140)\]

### MAX\_SCF\_HISTORY*: integer* *\= 0*

**Aliases:** MAX\_SCF\_HIST

**Lone keyword:** `1`

**Usage:** *MAX\_SCF\_HISTORY 1*

Maximum number of SCF iterations after the history pipeline is filled \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L146)\]

### NCOL\_BLOCK*: integer* *\= 32*

**Usage:** *NCOL\_BLOCK 31*

Sets the number of columns in a scalapack block \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L232)\]

### NROW\_BLOCK*: integer* *\= 32*

**Usage:** *NROW\_BLOCK 31*

sets the number of rows in a scalapack block \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L226)\]

### ROKS\_F*: real* *\= 5.00000000E-001*

**Aliases:** F\_ROKS

**Usage:** *ROKS\_F 1/2*

Allows to define the parameter f for the general ROKS scheme. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L258)\]

### ROKS\_PARAMETERS*: real\[6\]* *\= \-5.00000000E-001 1.50000000E+000 5.00000000E-001 5.00000000E-001 1.50000000E+000 \-5.00000000E-001*

**Aliases:** ROKS\_PARAMETER

**Usage:** *ROKS\_PARAMETERS 1/2 1/2 1/2 1/2 1/2 1/2*

Allows to define all parameters for the high-spin ROKS scheme explicitly. The full set of 6 parameters has to be specified in the order acc, bcc, aoo, boo, avv, bvv \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L271)\]

### ROKS\_SCHEME*: enum* *\= HIGH-SPIN*

**Usage:** *ROKS\_SCHEME HIGH-SPIN*

**Valid values:**

-   `GENERAL`

-   `HIGH-SPIN`


Selects the ROKS scheme when ROKS is applied. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L246)\]

### SCF\_GUESS*: enum* *\= ATOMIC*

**Usage:** *SCF\_GUESS RESTART*

**Valid values:**

-   `ATOMIC` Generate an atomic density using the atomic code and internal default values

-   `RESTART` Use the RESTART file as an initial guess (and ATOMIC if not present).

-   `RANDOM` Use random wavefunction coefficients.

-   `CORE` Diagonalize the core hamiltonian for an initial guess.

-   `HISTORY_RESTART` Extrapolated from previous RESTART files.

-   `MOPAC` Use same guess as MOPAC for semi-empirical methods or a simple diagonal density matrix for other methods

-   `EHT` Use the EHT (gfn0-xTB) code to generate an initial wavefunction.

-   `SPARSE` Generate a sparse wavefunction using the atomic code (for OT based methods)

-   `NONE` Skip initial guess (only for non-self consistent methods).


**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Selects how the initial wavefunction or density matrix is generated. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L207)\]
