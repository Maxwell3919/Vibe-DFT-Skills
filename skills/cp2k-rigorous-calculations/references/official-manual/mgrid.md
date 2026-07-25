# CP2K official manual snapshot: mgrid

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html
- Raw SHA-256: e4780f367dd1716fd4645893695016e14fe539b826ba7b4168d0941e8ce4b578
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# MGRID

Controls the multigrid used by GPW/GAPW to represent densities, potentials, and Gaussian products on real-space grids. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1245)\]

Subsections

-   [INTERPOLATOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID/INTERPOLATOR.html)
-   [RS\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID/RS_GRID.html)

## Keywords

-   [COMMENSURATE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.COMMENSURATE "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.COMMENSURATE")

-   **[CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.CUTOFF")**

-   [MULTIGRID\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.MULTIGRID_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.MULTIGRID_CUTOFF")

-   [MULTIGRID\_SET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.MULTIGRID_SET "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.MULTIGRID_SET")

-   **[NGRIDS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.NGRIDS "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.NGRIDS")**

-   **[PROGRESSION\_FACTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.PROGRESSION_FACTOR "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.PROGRESSION_FACTOR")**

-   [REALSPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.REALSPACE "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.REALSPACE")

-   **[REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.REL_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.REL_CUTOFF")**

-   [SKIP\_LOAD\_BALANCE\_DISTRIBUTED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.SKIP_LOAD_BALANCE_DISTRIBUTED "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.SKIP_LOAD_BALANCE_DISTRIBUTED")


## Keyword descriptions

### COMMENSURATE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *commensurate*

If the grids should be commensurate. If true overrides the progression factor and the cutoffs of the sub grids \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1276)\]

### CUTOFF*: real* *\= 2.80000000E+002 \[Ry\]*

**Usage:** *cutoff 300*

**Mentions:** ⭐[Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html), ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html), ⭐[Basis Sets](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/basis_sets.html), ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html), ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Plane-wave cutoff of the finest real-space grid level. Increasing this value improves the grid representation, but it is not a substitute for converging the Gaussian basis set. Default value for SE or DFTB calculation is 1.0 \[Ry\]. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1257)\]

### MULTIGRID\_CUTOFF*: real\[ \]* *\= \[Ry\]*

**Aliases:** CUTOFF\_LIST

**Usage:** *MULTIGRID\_CUTOFF 200.0 100.0*

List of cutoff values to set up multigrids manually \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1324)\]

### MULTIGRID\_SET*: logical* *\= F*

**Usage:** *MULTIGRID\_SET*

Activate a manual setting of the multigrids \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1302)\]

### NGRIDS*: integer* *\= 4*

**Usage:** *ngrids 1*

**Mentions:** ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html)

Number of multigrid levels. Smooth Gaussian products can be mapped to coarser levels, while sharper products require finer levels. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1250)\]

### PROGRESSION\_FACTOR*: real* *\= 3.00000000E+000*

**Usage:** *progression\_factor*

**Mentions:** ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html)

Factor used to derive the cutoff of coarser multigrid levels when they are not given explicitly. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1269)\]

### REALSPACE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *realspace*

If both rho and rho\_gspace are needed \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1284)\]

### REL\_CUTOFF*: real* *\= 4.00000000E+001 \[Ry\]*

**Aliases:** RELATIVE\_CUTOFF

**Usage:** *RELATIVE\_CUTOFF real*

**Mentions:** ⭐[Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html), ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Controls to which multigrid level a Gaussian product is mapped. It is the reference cutoff for a Gaussian with exponent alpha=1. Larger values keep more Gaussian products on finer grids and can be important for accurate energies, forces, stress tensors, and variable-cell simulations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1291)\]

### SKIP\_LOAD\_BALANCE\_DISTRIBUTED*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SKIP\_LOAD\_BALANCE\_DISTRIBUTED*

Skips load balancing on distributed multigrids. Memory usage is O(p) so may be used for all but the very largest runs. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1308)\]
