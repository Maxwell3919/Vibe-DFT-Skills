# CP2K official manual snapshot: kpoints

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html
- Raw SHA-256: d51fff85ac2d146cdc4d656682781a955e661b7e9278085dba2d207409091be2
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# KPOINTS

Controls Brillouin-zone sampling with k-points. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L79)\]

## Keywords

-   **[DEBUG\_FULL\_KPOINT\_SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.DEBUG_FULL_KPOINT_SYMMETRY "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.DEBUG_FULL_KPOINT_SYMMETRY")**

-   **[EPS\_SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.EPS_SYMMETRY "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.EPS_SYMMETRY")**

-   [FULL\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.FULL_GRID "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.FULL_GRID")

-   **[GAMMA\_CENTERED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.GAMMA_CENTERED "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.GAMMA_CENTERED")**

-   **[INVERSION\_SYMMETRY\_ONLY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.INVERSION_SYMMETRY_ONLY "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.INVERSION_SYMMETRY_ONLY")**

-   **[KPOINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.KPOINT "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.KPOINT")**

-   **[PARALLEL\_GROUP\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.PARALLEL_GROUP_SIZE "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.PARALLEL_GROUP_SIZE")**

-   **[SCHEME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SCHEME "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SCHEME")**

-   **[SYMMETRY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY")**

-   **[SYMMETRY\_BACKEND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY_BACKEND "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY_BACKEND")**

-   **[SYMMETRY\_REDUCTION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY_REDUCTION_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.SYMMETRY_REDUCTION_METHOD")**

-   **[UNITS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.UNITS "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.UNITS")**

-   **[VERBOSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.VERBOSE "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.VERBOSE")**

-   **[WAVEFUNCTIONS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html#CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.WAVEFUNCTIONS "CP2K_INPUT.FORCE_EVAL.DFT.KPOINTS.WAVEFUNCTIONS")**


## Keyword descriptions

### DEBUG\_FULL\_KPOINT\_SYMMETRY*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *DEBUG\_FULL\_KPOINT\_SYMMETRY*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Use full atomic k-point symmetry also for DEBUG finite-difference points. This is enabled by default so analytical and finite-difference evaluations use the symmetry of their current geometry. Disable it to restrict DEBUG finite-difference energies to inversion/time-reversal symmetry. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L153)\]

### EPS\_SYMMETRY*: real* *\= 1.00000000E-006*

**Aliases:** EPS\_GEO

**Usage:** *EPS\_SYMMETRY*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Accuracy in k-point symmetry determination. EPS\_GEO is accepted as an alias. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L203)\]

### FULL\_GRID*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *FULL\_GRID*

Use the full, non-symmetry-reduced k-point grid. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L138)\]

### GAMMA\_CENTERED*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *GAMMA\_CENTERED*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Generate a gamma-centered variant of the Monkhorst-Pack or MacDonald mesh. This shifts the original mesh so it can include the Gamma point, and makes sense only when an even number of subdivisions is used. For MacDonald meshes, the explicit shift is applied after the gamma-centering shift. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L103)\]

### INVERSION\_SYMMETRY\_ONLY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *INVERSION\_SYMMETRY\_ONLY*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Restrict k-point reduction to k-space inversion (time-reversal) symmetry. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L145)\]

### KPOINT*: real\[4\]*

**Keyword can be repeated.**

**Usage:** *KPOINT x y z w*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Specify kpoint coordinates and weight. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L114)\]

### PARALLEL\_GROUP\_SIZE*: integer* *\= \-1*

**Usage:** *PARALLEL\_GROUP\_SIZE*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Number of MPI processes to be used for a single k-point. This number must divide the total number of processes. The number of groups must divide the total number of kpoints. Value=-1 (smallest possible number of processes per group, satisfying the constraints). Value=0 (all processes). Value=n (exactly n processes). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L211)\]

### SCHEME*: string\[ \]*

**Usage:** *SCHEME {KPMETHOD} {integer} {integer} ..*

**References:** [Monkhorst1976](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#monkhorst1976), [MacDonald1978](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#macdonald1978)

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

K-point generation scheme. Available options are:

-   `NONE`

-   `GAMMA`

-   `MONKHORST-PACK`

-   `MACDONALD`

-   `GENERAL`


For `MONKHORST-PACK` the number of k points in all 3 dimensions has to be supplied along with the keyword. For `MACDONALD` also the list of shifts. E.g. `MONKHORST-PACK 12 12 8`, `MACDONALD 4 4 4 0.25 0.25 0.25`. `GENERAL` uses explicitly listed k-points. If symmetry reduction is requested, the explicit set must be equally weighted and closed under the selected operations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L84)\]

### SYMMETRY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SYMMETRY*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Use symmetry to reduce the number of kpoints. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L131)\]

### SYMMETRY\_BACKEND*: enum* *\= K290*

**Usage:** *SYMMETRY\_BACKEND K290*

**Valid values:**

-   `K290` Use the existing K290 k-point symmetry backend.

-   `SPGLIB` Use SPGLIB symmetry operations as k-point symmetry backend.


**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Select the backend used to provide and apply atomic k-point symmetry operations. K290 is the established default. SPGLIB uses the symmetry operations returned by SPGLIB, including their fractional translations. This applies to Monkhorst-Pack, MacDonald, and closed GENERAL k-point sets. If SYMMETRY\_REDUCTION\_METHOD is not specified, it follows the selected backend. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L163)\]

### SYMMETRY\_REDUCTION\_METHOD*: enum* *\= K290*

**Usage:** *SYMMETRY\_REDUCTION\_METHOD K290*

**Valid values:**

-   `K290` Use the existing K290 k-point symmetry reduction method.

-   `SPGLIB` Use SPGLIB symmetry operations for k-point reduction.


**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Select the method used to reduce Monkhorst-Pack and MacDonald k-point meshes when atomic symmetry is enabled. K290 is the established default. SPGLIB uses the symmetry operations returned by SPGLIB for the k-point reduction. GENERAL k-point lists can be reduced when the explicit set is equally weighted and closed under the selected operations. With SYMMETRY\_BACKEND K290 this can be used as a comparison mode using K290 operations for SPGLIB-generated mappings. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L179)\]

### UNITS*: string* *\= B\_VECTOR*

**Usage:** *UNITS*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Special k-points are defined either in units of reciprocal lattice vectors or in Cartesian coordinates in units of 2Pi/len. B\_VECTOR: in multiples of the reciprocal lattice vectors (b). CART\_ANGSTROM: In units of 2*Pi/Angstrom. CART\_BOHR: In units of 2*Pi/Bohr. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L121)\]

### VERBOSE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *VERBOSE*

**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Verbose output information. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L196)\]

### WAVEFUNCTIONS*: enum* *\= COMPLEX*

**Usage:** *WAVEFUNCTIONS REAL*

**Valid values:**

-   `REAL` Use real wavefunctions (if possible by kpoints specified).

-   `COMPLEX` Use complex wavefunctions (default).


**Mentions:** ⭐[K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)

Select whether real or complex wavefunctions should be used when allowed by the k-point set. REAL wavefunctions can only represent Gamma or special k-points and symmetry operations with real Bloch phases. Use COMPLEX for general atomic k-point symmetries with nontrivial phases. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_kpoints.F#L223)\]
