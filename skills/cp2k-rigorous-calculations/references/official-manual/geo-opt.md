# CP2K official manual snapshot: geo-opt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html
- Raw SHA-256: 70c0ee49a151de7bd6bd03d647cbaf2968a3981adb701f7c10d300d932712434
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# GEO\_OPT

This section sets the environment of the geometry optimizer. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L101)\]

Subsections

-   [BFGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT/BFGS.html)
-   [CG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT/CG.html)
-   [LBFGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT/LBFGS.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT/PRINT.html)
-   [TRANSITION\_STATE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT/TRANSITION_STATE.html)

## Keywords

-   [EPS\_SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.EPS_SYMMETRY "CP2K_INPUT.MOTION.GEO_OPT.EPS_SYMMETRY")

-   **[KEEP\_SPACE\_GROUP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.KEEP_SPACE_GROUP "CP2K_INPUT.MOTION.GEO_OPT.KEEP_SPACE_GROUP")**

-   [MAX\_DR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.MAX_DR "CP2K_INPUT.MOTION.GEO_OPT.MAX_DR")

-   **[MAX\_FORCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.MAX_FORCE "CP2K_INPUT.MOTION.GEO_OPT.MAX_FORCE")**

-   **[MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.MAX_ITER "CP2K_INPUT.MOTION.GEO_OPT.MAX_ITER")**

-   **[OPTIMIZER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.OPTIMIZER "CP2K_INPUT.MOTION.GEO_OPT.OPTIMIZER")**

-   **[RMS\_DR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.RMS_DR "CP2K_INPUT.MOTION.GEO_OPT.RMS_DR")**

-   [RMS\_FORCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.RMS_FORCE "CP2K_INPUT.MOTION.GEO_OPT.RMS_FORCE")

-   [SHOW\_SPACE\_GROUP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.SHOW_SPACE_GROUP "CP2K_INPUT.MOTION.GEO_OPT.SHOW_SPACE_GROUP")

-   [SPGR\_PRINT\_ATOMS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.SPGR_PRINT_ATOMS "CP2K_INPUT.MOTION.GEO_OPT.SPGR_PRINT_ATOMS")

-   [STEP\_START\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.STEP_START_VAL "CP2K_INPUT.MOTION.GEO_OPT.STEP_START_VAL")

-   [SYMM\_EXCLUDE\_RANGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.SYMM_EXCLUDE_RANGE "CP2K_INPUT.MOTION.GEO_OPT.SYMM_EXCLUDE_RANGE")

-   [SYMM\_REDUCTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.SYMM_REDUCTION "CP2K_INPUT.MOTION.GEO_OPT.SYMM_REDUCTION")

-   **[TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html#CP2K_INPUT.MOTION.GEO_OPT.TYPE "CP2K_INPUT.MOTION.GEO_OPT.TYPE")**


## Keyword descriptions

### EPS\_SYMMETRY*: real* *\= 1.00000000E-004*

**Usage:** *EPS\_SYMMETRY {REAL}*

Accuracy for space group determination. EPS\_SYMMETRY is dimensionless. Roughly speaking, two scaled (fractional) atomic positions v1, v2 are considered identical if |v1 - v2| < EPS\_SYMMETRY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L898)\]

### KEEP\_SPACE\_GROUP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KEEP\_SPACE\_GROUP .TRUE.*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Detect space group of the system and preserve it during optimization. The space group symmetry is applied to coordinates, forces, and the stress tensor. It works for supercell. It does not affect/reduce computational cost. Use EPS\_SYMMETRY to adjust the detection threshold. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L875)\]

### MAX\_DR*: real* *\= 3.00000000E-003 \[bohr\]*

**Usage:** *MAX\_DR {real}*

Convergence criterion for the maximum geometry change between the current and the last optimizer iteration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L837)\]

### MAX\_FORCE*: real* *\= 4.50000000E-004 \[bohr^-1\*hartree\]*

**Usage:** *MAX\_FORCE {real}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Simulating Vibronic Effects in Optical Spectra](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/vibronicspec.html)

Convergence criterion for the maximum force component of the current configuration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L845)\]

### MAX\_ITER*: integer* *\= 200*

**Usage:** *MAX\_ITER {integer}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Specifies the maximum number of geometry optimization steps. One step might imply several force evaluations for the CG and LBFGS optimizers. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L829)\]

### OPTIMIZER*: enum* *\= BFGS*

**Aliases:** MINIMIZER

**Usage:** *OPTIMIZER {BFGS|LBFGS|CG}*

**Valid values:**

-   `BFGS` Most efficient minimizer, but only for ‘small’ systems, as it relies on diagonalization of a full Hessian matrix

-   `LBFGS` Limited-memory variant of BFGS suitable for large systems. Not as well fine-tuned but can be more robust.

-   `CG` conjugate gradients, robust minimizer (depending on the line search) also OK for large systems


**References:** [Byrd1995](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#byrd1995)

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Specify which method to use to perform a geometry optimization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L813)\]

### RMS\_DR*: real* *\= 1.50000000E-003 \[bohr\]*

**Usage:** *RMS\_DR {real}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Convergence criterion for the root mean square (RMS) geometry change between the current and the last optimizer iteration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L852)\]

### RMS\_FORCE*: real* *\= 3.00000000E-004 \[bohr^-1\*hartree\]*

**Usage:** *RMS\_FORCE {real}*

Convergence criterion for the root mean square (RMS) force of the current configuration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L860)\]

### SHOW\_SPACE\_GROUP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SHOW\_SPACE\_GROUP .TRUE.*

Detect and show space group of the system after optimization. It works for supercell. It does not affect/reduce computational cost. Use EPS\_SYMMETRY to adjust the detection threshold. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L887)\]

### SPGR\_PRINT\_ATOMS*: logical* *\= F*

**Lone keyword:** `T`

Print equivalent atoms list for each space group symmetry operation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L929)\]

### STEP\_START\_VAL*: integer* *\= 0*

**Usage:** *step\_start\_val*

The starting step value for the GEO\_OPT module. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L867)\]

### SYMM\_EXCLUDE\_RANGE*: integer\[2\]*

**Keyword can be repeated.**

**Usage:** *SYMM\_EXCLUDE\_RANGE {Int} {Int}*

Range of atoms to exclude from space group symmetry. These atoms are excluded from both identification and enforcement. This keyword can be repeated. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L920)\]

### SYMM\_REDUCTION*: real\[3\]* *\= 0.00000000E+000 0.00000000E+000 0.00000000E+000*

**Usage:** *SYMM\_REDUCTION 0.0 0.0 0.0*

Direction of the external static electric field. Some symmetry operations are not compatible with the direction of an electric field. These operations are used when enforcing the space group. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L908)\]

### TYPE*: enum* *\= MINIMIZATION*

**Usage:** *TYPE (MINIMIZATION|TRANSITION\_STATE)*

**Valid values:**

-   `MINIMIZATION` Performs a geometry minimization.

-   `TRANSITION_STATE` Performs a transition state optimization.


**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Specify which kind of geometry optimization to perform \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L800)\]
