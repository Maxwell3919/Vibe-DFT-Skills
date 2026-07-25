# CP2K official manual snapshot: scf-ot

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html
- Raw SHA-256: 7cbb09ce82c7db6537f4c7b4fbdbcd6e057fb675fe99ffb9c221682d6777d869
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# OT

**References:** [VandeVondele2003](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2003), [Weber2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#weber2008)

Sets the various options for the orbital transformation (OT) method. Default settings already provide an efficient, yet robust method. Most systems benefit from using the FULL\_ALL preconditioner combined with a small value (0.001) of ENERGY\_GAP. Well-behaved systems might benefit from using a DIIS minimizer.

**Advantages:** It’s fast, because no expensive diagonalisation is performed. If preconditioned correctly, method guaranteed to find minimum.

**Disadvantages:** Sensitive to preconditioning. A good preconditioner can be expensive. No smearing, or advanced SCF mixing possible: POOR convergence for metallic systems. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L558)\]

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.SECTION_PARAMETERS")

-   **[ALGORITHM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ALGORITHM "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ALGORITHM")**

-   [BROYDEN\_ADAPTIVE\_SIGMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ADAPTIVE_SIGMA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ADAPTIVE_SIGMA")

-   [BROYDEN\_BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_BETA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_BETA")

-   [BROYDEN\_ENABLE\_FLIP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ENABLE_FLIP "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ENABLE_FLIP")

-   [BROYDEN\_ETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ETA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_ETA")

-   [BROYDEN\_FORGET\_HISTORY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_FORGET_HISTORY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_FORGET_HISTORY")

-   [BROYDEN\_GAMMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_GAMMA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_GAMMA")

-   [BROYDEN\_OMEGA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_OMEGA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_OMEGA")

-   [BROYDEN\_SIGMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA")

-   [BROYDEN\_SIGMA\_DECREASE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA_DECREASE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA_DECREASE")

-   [BROYDEN\_SIGMA\_MIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA_MIN "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.BROYDEN_SIGMA_MIN")

-   [CHOLESKY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.CHOLESKY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.CHOLESKY")

-   [ENERGIES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ENERGIES "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ENERGIES")

-   [ENERGY\_GAP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ENERGY_GAP "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ENERGY_GAP")

-   [EPS\_IRAC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC")

-   [EPS\_IRAC\_FILTER\_MATRIX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_FILTER_MATRIX "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_FILTER_MATRIX")

-   [EPS\_IRAC\_QUICK\_EXIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_QUICK_EXIT "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_QUICK_EXIT")

-   [EPS\_IRAC\_SWITCH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_SWITCH "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_IRAC_SWITCH")

-   [EPS\_TAYLOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_TAYLOR "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.EPS_TAYLOR")

-   [GOLD\_TARGET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.GOLD_TARGET "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.GOLD_TARGET")

-   [IRAC\_DEGREE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.IRAC_DEGREE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.IRAC_DEGREE")

-   **[LINESEARCH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.LINESEARCH "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.LINESEARCH")**

-   [MAX\_IRAC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_IRAC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_IRAC")

-   [MAX\_SCF\_DIIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_SCF_DIIS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_SCF_DIIS")

-   [MAX\_TAYLOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_TAYLOR "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MAX_TAYLOR")

-   **[MINIMIZER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MINIMIZER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.MINIMIZER")**

-   [NONDIAG\_ENERGY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.NONDIAG_ENERGY "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.NONDIAG_ENERGY")

-   [NONDIAG\_ENERGY\_STRENGTH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.NONDIAG_ENERGY_STRENGTH "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.NONDIAG_ENERGY_STRENGTH")

-   [N\_HISTORY\_VEC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.N_HISTORY_VEC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.N_HISTORY_VEC")

-   [OCCUPATION\_PRECONDITIONER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.OCCUPATION_PRECONDITIONER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.OCCUPATION_PRECONDITIONER")

-   [ON\_THE\_FLY\_LOC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ON_THE_FLY_LOC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ON_THE_FLY_LOC")

-   [ORTHO\_IRAC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ORTHO_IRAC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ORTHO_IRAC")

-   **[PRECONDITIONER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.PRECONDITIONER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.PRECONDITIONER")**

-   [PRECOND\_SOLVER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.PRECOND_SOLVER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.PRECOND_SOLVER")

-   [ROTATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ROTATION "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.ROTATION")

-   [SAFE\_DIIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.SAFE_DIIS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.SAFE_DIIS")

-   [STEPSIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.STEPSIZE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OT.STEPSIZE")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&OT T*

controls the activation of the ot method \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L575)\]

### ALGORITHM*: enum* *\= STRICT*

**Usage:** *ALGORITHM STRICT*

**Valid values:**

-   `STRICT` Strict orthogonality: Taylor or diagonalization based algorithm.

-   `IRAC` Orbital Transformation based Iterative Refinement of the Approximative Congruence transformation (OT/IR).


**References:** [VandeVondele2003](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2003), [VandeVondele2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2005), [Weber2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#weber2008)

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Algorithm to be used for OT \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L583)\]

### BROYDEN\_ADAPTIVE\_SIGMA*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *BROYDEN\_ADAPTIVE\_SIGMA ON*

Enable adaptive curvature estimation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L752)\]

### BROYDEN\_BETA*: real* *\= 9.00000000E-001*

**Usage:** *BROYDEN\_BETA 0.9*

Underrelaxation for the broyden mixer \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L696)\]

### BROYDEN\_ENABLE\_FLIP*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *BROYDEN\_ENABLE\_FLIP ON*

Ensure positive definite update \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L759)\]

### BROYDEN\_ETA*: real* *\= 7.00000000E-001*

**Usage:** *BROYDEN\_ETA 0.7*

Dampening of estimated energy curvature. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L717)\]

### BROYDEN\_FORGET\_HISTORY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *BROYDEN\_FORGET\_HISTORY OFF*

Forget history on bad approximation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L745)\]

### BROYDEN\_GAMMA*: real* *\= 5.00000000E-001*

**Usage:** *BROYDEN\_GAMMA 0.5*

Backtracking parameter \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L703)\]

### BROYDEN\_OMEGA*: real* *\= 1.10000000E+000*

**Usage:** *BROYDEN\_OMEGA 1.1*

Growth limit of curvature. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L724)\]

### BROYDEN\_SIGMA*: real* *\= 2.50000000E-001*

**Usage:** *BROYDEN\_SIGMA 0.25*

Curvature of energy functional. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L710)\]

### BROYDEN\_SIGMA\_DECREASE*: real* *\= 7.00000000E-001*

**Usage:** *BROYDEN\_SIGMA\_DECREASE 0.7*

Reduction of curvature on bad approximation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L731)\]

### BROYDEN\_SIGMA\_MIN*: real* *\= 5.00000000E-002*

**Usage:** *BROYDEN\_SIGMA\_MIN 0.05*

Minimum adaptive curvature. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L738)\]

### CHOLESKY*: enum* *\= REDUCE*

**Usage:** *CHOLESKY REDUCE*

**Valid values:**

-   `OFF` The cholesky algorithm is not used

-   `REDUCE` Reduce is called

-   `RESTORE` Reduce is replaced by two restore

-   `INVERSE` Restore uses operator multiply by inverse of the triangular matrix

-   `INVERSE_DBCSR` Like inverse, but matrix stored as dbcsr, sparce matrix algebra used when possible


If FULL\_ALL the cholesky decomposition of the S matrix is used. Options on the algorithm to be used. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L831)\]

### ENERGIES*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ENERGIES*

Optimize orbital energies for use in Fermi-Dirac smearing (requires ROTATION and FD smearing to be active). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L904)\]

### ENERGY\_GAP*: real* *\= \-1.00000000E+000*

**Usage:** *ENERGY\_GAP 0.001*

Should be an estimate for the energy gap \[a.u.\] (HOMO-LUMO) and is used in preconditioning, especially effective with the FULL\_ALL preconditioner, in which case it should be an underestimate of the gap (can be a small number, e.g. 0.002). FULL\_SINGLE\_INVERSE takes it as lower bound (values below 0.05 can cause stability issues). In general, higher values will tame the preconditioner in case of poor initial guesses. A negative value will leave the choice to CP2K depending on type of preconditioner. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L864)\]

### EPS\_IRAC*: real* *\= 1.00000000E-010*

**Usage:** *EPS\_IRAC 1.0E-5*

Targeted accuracy during the refinement iteration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L627)\]

### EPS\_IRAC\_FILTER\_MATRIX*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_IRAC\_FILTER\_MATRIX 1.0E-5*

Sets the threshold for filtering the matrices. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L620)\]

### EPS\_IRAC\_QUICK\_EXIT*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_IRAC\_QUICK\_EXIT 1.0E-2*

Only one extra refinement iteration is done when the norm is below this value. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L634)\]

### EPS\_IRAC\_SWITCH*: real* *\= 1.00000000E-002*

**Usage:** *EPS\_IRAC\_SWITCH 1.0E-3*

The algorithm switches to the polynomial refinement when the norm is below this value. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L642)\]

### EPS\_TAYLOR*: real* *\= 1.00000000E-016*

**Aliases:** EPSTAYLOR

**Usage:** *EPS\_TAYLOR 1.0E-15*

Target accuracy of the taylor expansion for the matrix functions, should normally be kept as is. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L877)\]

### GOLD\_TARGET*: real* *\= 1.00000000E-002*

**Usage:** *GOLD\_TARGET 0.1*

Target relative uncertainty in the location of the minimum for LINESEARCH GOLD \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L797)\]

### IRAC\_DEGREE*: integer* *\= 4*

**Usage:** *IRAC\_DEGREE 4*

The refinement polynomial degree (2, 3 or 4). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L596)\]

### LINESEARCH*: enum* *\= 2PNT*

**Aliases:** LINE\_SEARCH

**Usage:** *LINESEARCH GOLD*

**Valid values:**

-   `ADAPT` extrapolates usually based on 3 points, uses additional points on demand, very robust.

-   `NONE` always take steps of fixed length

-   `2PNT` extrapolate based on 2 points

-   `3PNT` extrapolate based on 3 points

-   `GOLD` perform 1D golden section search of the minimum (very expensive)


**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

1D line search algorithm to be used with the OT minimizer, in increasing order of robustness and cost. MINIMIZER CG combined with LINESEARCH GOLD should always find an electronic minimum. Whereas the 2PNT minimizer is almost always OK, 3PNT might be needed for systems in which successive OT CG steps do not decrease the total energy. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L766)\]

### MAX\_IRAC*: integer* *\= 50*

**Usage:** *MAX\_IRAC 5*

Maximum allowed refinement iteration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L603)\]

### MAX\_SCF\_DIIS*: integer* *\= 0*

**Usage:** *MAX\_SCF\_DIIS 20*

Maximum DIIS SCF inner loop cycles. This can be used to extend SCF cycles after a switch to DIIS (see eps\_diis). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L680)\]

### MAX\_TAYLOR*: integer* *\= 4*

**Usage:** *MAX\_TAYLOR 5*

Maximum order of the Taylor expansion before diagonalisation is preferred, for large parallel runs a slightly higher order could sometimes result in a small speedup. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L886)\]

### MINIMIZER*: enum* *\= CG*

**Usage:** *MINIMIZER DIIS*

**Valid values:**

-   `SD` Steepest descent: not recommended

-   `CG` Conjugate Gradients: most reliable, use for difficult systems. The total energy should decrease at every OT CG step if the line search is appropriate.

-   `DIIS` Direct inversion in the iterative subspace: less reliable than CG, but sometimes about 50% faster

-   `BROYDEN` Broyden mixing approximating the inverse Hessian


**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Minimizer to be used with the OT method \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L659)\]

### NONDIAG\_ENERGY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *NONDIAG\_ENERGY*

Add a non-diagonal energy penalty (FD smearing) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L919)\]

### NONDIAG\_ENERGY\_STRENGTH*: real* *\= 1.00000000E+000*

**Usage:** *NONDIAG\_ENERGY\_STRENGTH*

The prefactor for the non-diagonal energy penalty (FD smearing) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L926)\]

### N\_HISTORY\_VEC*: integer* *\= 7*

**Aliases:** NDIIS ,N\_DIIS ,N\_BROYDEN

**Usage:** *N\_DIIS 4*

Number of history vectors to be used with DIIS or BROYDEN \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L688)\]

### OCCUPATION\_PRECONDITIONER*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *OCCUPATION\_PRECONDITIONER*

Preconditioner with the occupation numbers (FD smearing) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L912)\]

### ON\_THE\_FLY\_LOC*: logical* *\= F*

**Usage:** *ON\_THE\_FLY\_LOC T*

On the fly localization of the molecular orbitals. Can only be used with OT/IRAC. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L650)\]

### ORTHO\_IRAC*: enum* *\= CHOL*

**Usage:** *ORTHO\_IRAC POLY*

**Valid values:**

-   `CHOL` Cholesky.

-   `POLY` Polynomial.

-   `LWDN` Loewdin.


The orthogonality method. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L610)\]

### PRECONDITIONER*: enum* *\= FULL\_KINETIC*

**Usage:** *PRECONDITIONER FULL\_ALL*

**Valid values:**

-   `FULL_ALL` Most effective state selective preconditioner based on diagonalization, requires the ENERGY\_GAP parameter to be an underestimate of the HOMO-LUMO gap. This preconditioner is recommended for almost all systems, except very large systems where make\_preconditioner would dominate the total computational cost.

-   `FULL_SINGLE_INVERSE` Based on H-eS cholesky inversion, similar to FULL\_SINGLE in preconditioning efficiency but cheaper to construct, might be somewhat less robust. Recommended for large systems.

-   `FULL_SINGLE` Based on H-eS diagonalisation, not as good as FULL\_ALL, but somewhat cheaper to apply.

-   `FULL_KINETIC` Cholesky inversion of S and T, fast construction, robust, and relatively good, use for very large systems.

-   `FULL_S_INVERSE` Cholesky inversion of S, not as good as FULL\_KINETIC, yet equally expensive.

-   `NONE` skip preconditioning


**References:** [VandeVondele2003](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2003), [Weber2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#weber2008), [Schiffmann2015](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#schiffmann2015)

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Type of preconditioner to be used with all minimization schemes. They differ in effectiveness, cost of construction, cost of application. Properly preconditioned minimization can be orders of magnitude faster than doing nothing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L805)\]

### PRECOND\_SOLVER*: enum* *\= DEFAULT*

**Usage:** *PRECOND\_SOLVER DIRECT*

**Valid values:**

-   `DEFAULT` the default

-   `DIRECT` Cholesky decomposition followed by triangular solve (works for FULL\_KINETIC/SINGLE\_INVERSE/S\_INVERSE)

-   `INVERSE_CHOLESKY` Cholesky decomposition followed by explicit inversion (works for FULL\_KINETIC/SINGLE\_INVERSE/S\_INVERSE)

-   `INVERSE_UPDATE` Performs a Hotelling update of the inverse if a previous preconditioner is present. Mainly useful for GPU accelerated systems (works for FULL\_KINETIC/SINGLE\_INVERSE/S\_INVERSE)


How the preconditioner is applied to the residual. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L845)\]

### ROTATION*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ROTATION*

Introduce additional variables so that rotations of the occupied subspace are allowed as well, only needed for cases where the energy is not invariant under a rotation of the occupied subspace such as non-singlet restricted calculations or fractional occupations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L894)\]

### SAFE\_DIIS*: logical* *\= T*

**Aliases:** SAFER\_DIIS

**Usage:** *SAFE\_DIIS ON*

Reject DIIS steps if they point away from the minimum, do SD in that case. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L672)\]

### STEPSIZE*: real* *\= \-1.00000000E+000*

**Usage:** *STEPSIZE 0.4*

Initial stepsize used for the line search, sometimes this parameter can be reduced to stabilize DIIS or to improve the CG behavior in the first few steps. The optimal value depends on the quality of the preconditioner. A negative values leaves the choice to CP2K depending on the preconditioner. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L787)\]
