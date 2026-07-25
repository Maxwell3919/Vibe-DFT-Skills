# CP2K official manual snapshot: outer-scf

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html
- Raw SHA-256: b54632d02f2a1290cff9f07157ca744d99cf5217910f71a8d472e1fb0e4f5711
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# OUTER\_SCF

Controls an outer SCF loop, often used to stabilize difficult OT convergence, constraints, or other variables wrapped around the inner SCF cycle. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L436)\]

Subsections

-   [CDFT\_OPT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF/CDFT_OPT.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.SECTION_PARAMETERS")

-   [BISECT\_TRUST\_COUNT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.BISECT_TRUST_COUNT "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.BISECT_TRUST_COUNT")

-   [DIIS\_BUFFER\_LENGTH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.DIIS_BUFFER_LENGTH "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.DIIS_BUFFER_LENGTH")

-   [EPS\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.EPS_SCF "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.EPS_SCF")

-   [EXTRAPOLATION\_ORDER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.EXTRAPOLATION_ORDER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.EXTRAPOLATION_ORDER")

-   **[MAX\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.MAX_SCF "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.MAX_SCF")**

-   [OPTIMIZER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.OPTIMIZER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.OPTIMIZER")

-   [STEP\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.STEP_SIZE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.STEP_SIZE")

-   [TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.TYPE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.OUTER_SCF.TYPE")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&OUTER\_SCF ON*

Activates the outer SCF loop. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L443)\]

### BISECT\_TRUST\_COUNT*: integer* *\= 10*

**Usage:** *BISECT\_TRUST\_COUNT 5*

Maximum number of times the same point will be used in bisection, a small number guards against the effect of wrongly converged states. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L499)\]

### DIIS\_BUFFER\_LENGTH*: integer* *\= 3*

**Usage:** *DIIS\_BUFFER\_LENGTH 5*

Maximum number of DIIS vectors used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L516)\]

### EPS\_SCF*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_SCF 1.0E-6*

The target gradient of the outer SCF variables. Notice that the EPS\_SCF of the inner loop also determines the value that can be reached in the outer loop, typically EPS\_SCF of the outer loop must be smaller than or equal to EPS\_SCF of the inner loop. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L506)\]

### EXTRAPOLATION\_ORDER*: integer* *\= 3*

**Usage:** *EXTRAPOLATION\_ORDER 5*

Number of past states used in the extrapolation of the variables during e.g. MD \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L522)\]

### MAX\_SCF*: integer* *\= 50*

**Usage:** *MAX\_SCF 20*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Maximum number of outer SCF loops. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L528)\]

### OPTIMIZER*: enum* *\= NONE*

**Usage:** *OPTIMIZER SD*

**Valid values:**

-   `SD` Takes steps in the direction of the gradient, multiplied by step\_size

-   `DIIS` Uses a Direct Inversion in the Iterative Subspace method

-   `NONE` Do nothing, useful only with the none type

-   `BISECT` Bisection of the gradient, useful for difficult one dimensional cases

-   `BROYDEN` Broyden’s method. Variant defined in BROYDEN\_TYPE.

-   `NEWTON` Newton’s method. Only compatible with CDFT constraints.

-   `SECANT` Secant method. Only for one dimensional cases. See Broyden for multidimensional cases.

-   `NEWTON_LS` Newton’s method with backtracking line search to find the optimal step size. Only compatible with CDFT constraints. Starts from the regular Newton solution and successively reduces the step size until the L2 norm of the CDFT gradient decreases or MAX\_LS steps is reached. Potentially very expensive because each iteration performs a full SCF calculation.


Method used to bring the outer loop to a stationary point \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L474)\]

### STEP\_SIZE*: real* *\= 5.00000000E-001*

**Usage:** *STEP\_SIZE -1.0*

The initial step\_size used in the optimizer (currently steepest descent). Note that in cases where a sadle point is sought for (constrained DFT), this can be negative. For Newton and Broyden optimizers, use a value less/higher than the default 1.0 (in absolute value, the sign is not significant) to active an under/overrelaxed optimizer. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L534)\]

### TYPE*: enum* *\= NONE*

**Usage:** *TYPE DDAPC\_CONSTRAINT*

**Valid values:**

-   `DDAPC_CONSTRAINT` Enforce a constraint on the DDAPC, requires the corresponding section

-   `S2_CONSTRAINT` Enforce a constraint on the S2, requires the corresponding section

-   `BASIS_CENTER_OPT` Optimize positions of basis functions, if atom types FLOATING\_BASIS\_CENTER are defined

-   `CDFT_CONSTRAINT` Enforce a constraint on a generic CDFT weight population. Requires the corresponding section QS&CDFT which determines the type of weight used.

-   `NONE` Do nothing in the outer loop, useful for resetting the inner loop,


Specifies which kind of outer SCF should be employed \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L455)\]
