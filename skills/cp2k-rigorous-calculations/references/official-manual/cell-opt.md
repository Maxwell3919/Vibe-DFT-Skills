# CP2K official manual snapshot: cell-opt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html
- Raw SHA-256: d1e0a0b3d2e46b929b4fae44d6e9fbfcef6e065180fe56b8a9d291ef704c25d0
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# CELL\_OPT

This section sets the environment for the optimization of the simulation cell. As is noted in FORCE\_EVAL/SUBSYS/CELL, the program convention is that the first cell vector A lies along the X-axis and the second cell vector B is in the XY plane, such that the cell vector matrix is a lower triangle. There is no complete, official algorithm support and/or tests for updating the three upper triangular components during a cell optimization; please prepare input accordingly with these three components precisely 0 even for cases like the primitive rhombohedral cell of the FCC lattice. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1019)\]

Subsections

-   [BFGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT/BFGS.html)
-   [CG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT/CG.html)
-   [LBFGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT/LBFGS.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT/PRINT.html)

## Keywords

-   **[CONSTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.CONSTRAINT "CP2K_INPUT.MOTION.CELL_OPT.CONSTRAINT")**

-   [EPS\_SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.EPS_SYMMETRY "CP2K_INPUT.MOTION.CELL_OPT.EPS_SYMMETRY")

-   **[EXTERNAL\_PRESSURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.EXTERNAL_PRESSURE "CP2K_INPUT.MOTION.CELL_OPT.EXTERNAL_PRESSURE")**

-   **[KEEP\_ANGLES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.KEEP_ANGLES "CP2K_INPUT.MOTION.CELL_OPT.KEEP_ANGLES")**

-   **[KEEP\_SPACE\_GROUP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.KEEP_SPACE_GROUP "CP2K_INPUT.MOTION.CELL_OPT.KEEP_SPACE_GROUP")**

-   **[KEEP\_SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.KEEP_SYMMETRY "CP2K_INPUT.MOTION.CELL_OPT.KEEP_SYMMETRY")**

-   **[KEEP\_VOLUME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.KEEP_VOLUME "CP2K_INPUT.MOTION.CELL_OPT.KEEP_VOLUME")**

-   [MAX\_DR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.MAX_DR "CP2K_INPUT.MOTION.CELL_OPT.MAX_DR")

-   [MAX\_FORCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.MAX_FORCE "CP2K_INPUT.MOTION.CELL_OPT.MAX_FORCE")

-   [MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.MAX_ITER "CP2K_INPUT.MOTION.CELL_OPT.MAX_ITER")

-   **[OPTIMIZER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.OPTIMIZER "CP2K_INPUT.MOTION.CELL_OPT.OPTIMIZER")**

-   **[PRESSURE\_TOLERANCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.PRESSURE_TOLERANCE "CP2K_INPUT.MOTION.CELL_OPT.PRESSURE_TOLERANCE")**

-   [RMS\_DR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.RMS_DR "CP2K_INPUT.MOTION.CELL_OPT.RMS_DR")

-   [RMS\_FORCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.RMS_FORCE "CP2K_INPUT.MOTION.CELL_OPT.RMS_FORCE")

-   [SHOW\_SPACE\_GROUP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.SHOW_SPACE_GROUP "CP2K_INPUT.MOTION.CELL_OPT.SHOW_SPACE_GROUP")

-   [SPGR\_PRINT\_ATOMS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.SPGR_PRINT_ATOMS "CP2K_INPUT.MOTION.CELL_OPT.SPGR_PRINT_ATOMS")

-   [STEP\_START\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.STEP_START_VAL "CP2K_INPUT.MOTION.CELL_OPT.STEP_START_VAL")

-   [SYMM\_EXCLUDE\_RANGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.SYMM_EXCLUDE_RANGE "CP2K_INPUT.MOTION.CELL_OPT.SYMM_EXCLUDE_RANGE")

-   [SYMM\_REDUCTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html#CP2K_INPUT.MOTION.CELL_OPT.SYMM_REDUCTION "CP2K_INPUT.MOTION.CELL_OPT.SYMM_REDUCTION")


## Keyword descriptions

### CONSTRAINT*: enum* *\= NONE*

**Usage:** *CONSTRAINT (none|x|y|z|xy|xz|yz)*

**Valid values:**

-   `NONE` Fix nothing

-   `X` Fix only x component

-   `Y` Fix only y component

-   `Z` Fix only z component

-   `XY` Fix x and y component

-   `XZ` Fix x and z component

-   `YZ` Fix y and z component


**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Imposes a constraint on the pressure tensor by fixing the specified cell components. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1084)\]

### EPS\_SYMMETRY*: real* *\= 1.00000000E-004*

**Usage:** *EPS\_SYMMETRY {REAL}*

Accuracy for space group determination. EPS\_SYMMETRY is dimensionless. Roughly speaking, two scaled (fractional) atomic positions v1, v2 are considered identical if |v1 - v2| < EPS\_SYMMETRY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L898)\]

### EXTERNAL\_PRESSURE*: real\[ \]* *\= 1.00000000E+002 0.00000000E+000 0.00000000E+000 0.00000000E+000 1.00000000E+002 0.00000000E+000 0.00000000E+000 0.00000000E+000 1.00000000E+002 \[bar\]*

**Usage:** *EXTERNAL\_PRESSURE {REAL} .. {REAL}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Specifies the external pressure (1 value or the full 9 components of the pressure tensor) applied during the cell optimization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1042)\]

### KEEP\_ANGLES*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KEEP\_ANGLES TRUE*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Keep angles between the cell vectors constant, but allow the lengths of the cell vectors to change independently during cell optimization. This is implemented by projecting out the components of angles in the cell gradient before the cell is updated. Albeit general, this is most useful for triclinic cells; to enforce higher symmetry, see KEEP\_SYMMETRY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1061)\]

### KEEP\_SPACE\_GROUP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KEEP\_SPACE\_GROUP .TRUE.*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Detect space group of the system and preserve it during optimization. The space group symmetry is applied to coordinates, forces, and the stress tensor. It works for supercell. It does not affect/reduce computational cost. Use EPS\_SYMMETRY to adjust the detection threshold. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L875)\]

### KEEP\_SYMMETRY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KEEP\_SYMMETRY TRUE*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Keep the requested initial cell symmetry as specified in the FORCE\_EVAL/SUBSYS/CELL section during cell optimization. This is implemented by removing symmetry-breaking components and taking averages of components if necessary in the cell gradient before the cell is updated. To enforce the space group (which requires spglib package), see KEEP\_SPACE\_GROUP. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1072)\]

### KEEP\_VOLUME*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KEEP\_VOLUME TRUE*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Keep the volume of the cell constant during cell optimization. This is implemented by comparing the cell volumes and scaling the new cell vectors just before updating the cell information, and can be used together with KEEP\_ANGLES or KEEP\_SYMMETRY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1052)\]

### MAX\_DR*: real* *\= 3.00000000E-003 \[bohr\]*

**Usage:** *MAX\_DR {real}*

Convergence criterion for the maximum geometry change between the current and the last optimizer iteration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L837)\]

### MAX\_FORCE*: real* *\= 4.50000000E-004 \[bohr^-1\*hartree\]*

**Usage:** *MAX\_FORCE {real}*

Convergence criterion for the maximum force component of the current configuration. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L845)\]

### MAX\_ITER*: integer* *\= 200*

**Usage:** *MAX\_ITER {integer}*

Specifies the maximum number of geometry optimization steps. One step might imply several force evaluations for the CG and LBFGS optimizers. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L829)\]

### OPTIMIZER*: enum* *\= BFGS*

**Aliases:** MINIMIZER

**Usage:** *OPTIMIZER {BFGS|LBFGS|CG}*

**Valid values:**

-   `BFGS` Most efficient minimizer, but only for ‘small’ systems, as it relies on diagonalization of a full Hessian matrix

-   `LBFGS` Limited-memory variant of BFGS suitable for large systems. Not as well fine-tuned but can be more robust.

-   `CG` conjugate gradients, robust minimizer (depending on the line search) also OK for large systems


**References:** [Byrd1995](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#byrd1995)

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html)

Specify which method to use to perform a geometry optimization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L813)\]

### PRESSURE\_TOLERANCE*: real* *\= 1.00000000E+002 \[bar\]*

**Usage:** *PRESSURE\_TOLERANCE {REAL}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Specifies the Pressure tolerance (compared to the external pressure) to achieve during the cell optimization. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L1100)\]

### RMS\_DR*: real* *\= 1.50000000E-003 \[bohr\]*

**Usage:** *RMS\_DR {real}*

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

The starting step value for the CELL\_OPT module. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L867)\]

### SYMM\_EXCLUDE\_RANGE*: integer\[2\]*

**Keyword can be repeated.**

**Usage:** *SYMM\_EXCLUDE\_RANGE {Int} {Int}*

Range of atoms to exclude from space group symmetry. These atoms are excluded from both identification and enforcement. This keyword can be repeated. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L920)\]

### SYMM\_REDUCTION*: real\[3\]* *\= 0.00000000E+000 0.00000000E+000 0.00000000E+000*

**Usage:** *SYMM\_REDUCTION 0.0 0.0 0.0*

Direction of the external static electric field. Some symmetry operations are not compatible with the direction of an electric field. These operations are used when enforcing the space group. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k_motion.F#L908)\]
