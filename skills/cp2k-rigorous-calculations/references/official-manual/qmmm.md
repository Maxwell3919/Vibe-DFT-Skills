# CP2K official manual snapshot: qmmm

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html
- Raw SHA-256: 88e6bcdbca17648050d81004bc3fd773f06eafe8d4c17173704140e4d036848f
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# QMMM

**References:** [Laino2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#laino2005), [Laino2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#laino2006)

Controls QM/MM calculations, including mechanical, electrostatic, Gaussian-expanded, and periodic embedding options. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L97)\]

Subsections

-   [CELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/CELL.html)
-   [FORCEFIELD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/FORCEFIELD.html)
-   [FORCE\_MIXING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/FORCE_MIXING.html)
-   [IMAGE\_CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/IMAGE_CHARGE.html)
-   [INTERPOLATOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/INTERPOLATOR.html)
-   [LINK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/LINK.html)
-   [MM\_KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/MM_KIND.html)
-   [PERIODIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/PERIODIC.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/PRINT.html)
-   [QM\_KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/QM_KIND.html)
-   [WALLS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM/WALLS.html)

## Keywords

-   [CENTER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.CENTER "CP2K_INPUT.FORCE_EVAL.QMMM.CENTER")

-   [CENTER\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.CENTER_GRID "CP2K_INPUT.FORCE_EVAL.QMMM.CENTER_GRID")

-   [CENTER\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.CENTER_TYPE "CP2K_INPUT.FORCE_EVAL.QMMM.CENTER_TYPE")

-   [DELTA\_CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.DELTA_CHARGE "CP2K_INPUT.FORCE_EVAL.QMMM.DELTA_CHARGE")

-   [EPS\_MM\_RSPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.EPS_MM_RSPACE "CP2K_INPUT.FORCE_EVAL.QMMM.EPS_MM_RSPACE")

-   **[E\_COUPL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.E_COUPL "CP2K_INPUT.FORCE_EVAL.QMMM.E_COUPL")**

-   [INITIAL\_TRANSLATION\_VECTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.INITIAL_TRANSLATION_VECTOR "CP2K_INPUT.FORCE_EVAL.QMMM.INITIAL_TRANSLATION_VECTOR")

-   [MM\_POTENTIAL\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.MM_POTENTIAL_FILE_NAME "CP2K_INPUT.FORCE_EVAL.QMMM.MM_POTENTIAL_FILE_NAME")

-   [NOCOMPATIBILITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.NOCOMPATIBILITY "CP2K_INPUT.FORCE_EVAL.QMMM.NOCOMPATIBILITY")

-   [PARALLEL\_SCHEME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.PARALLEL_SCHEME "CP2K_INPUT.FORCE_EVAL.QMMM.PARALLEL_SCHEME")

-   [SPHERICAL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.SPHERICAL_CUTOFF "CP2K_INPUT.FORCE_EVAL.QMMM.SPHERICAL_CUTOFF")

-   [USE\_GEEP\_LIB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html#CP2K_INPUT.FORCE_EVAL.QMMM.USE_GEEP_LIB "CP2K_INPUT.FORCE_EVAL.QMMM.USE_GEEP_LIB")


## Keyword descriptions

### CENTER*: enum* *\= EVERY\_STEP*

**Usage:** *center (EVERY\_STEP|SETUP\_ONLY|NEVER)*

**Valid values:**

-   `EVERY_STEP` Re-center every step

-   `SETUP_ONLY` Center at first step only

-   `NEVER` Never center


This keyword sets when the QM system is automatically centered. Default is EVERY\_STEP. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L182)\]

### CENTER\_GRID*: logical* *\= F*

**Usage:** *CENTER\_GRID LOGICAL*

This keyword specifies whether the QM system is centered in units of the grid spacing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L206)\]

### CENTER\_TYPE*: enum* *\= MAX\_MINUS\_MIN*

**Usage:** *center\_type (MAX\_MINUS\_MIN|PBC\_AWARE\_MAX\_MINUS\_MIN)*

**Valid values:**

-   `MAX_MINUS_MIN` Center of box defined by maximum coordinate minus minimum coordinate

-   `PBC_AWARE_MAX_MINUS_MIN` PBC-aware centering (useful for &QMMM&FORCE\_MIXING)


This keyword specifies how to do the QM system centering. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L195)\]

### DELTA\_CHARGE*: integer* *\= 0*

**Usage:** *DELTA\_CHARGE q*

Additional net charge relative to that specified in DFT section. Used automatically by force mixing \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L221)\]

### EPS\_MM\_RSPACE*: real* *\= 1.00000000E-010*

**Usage:** *eps\_mm\_rspace real*

Set the threshold for the collocation of the GEEP gaussian functions. this keyword affects only the GAUSS E\_COUPLING. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L148)\]

### E\_COUPL*: enum* *\= NONE*

**Aliases:** QMMM\_COUPLING ,ECOUPL

**Usage:** *E\_COUPL GAUSS*

**Valid values:**

-   `NONE` Mechanical coupling (i.e. classical point charge based)

-   `COULOMB` Using analytical 1/r potential (Coulomb) - not available for GPW/GAPW

-   `GAUSS` Using fast Gaussian expansion of the electrostatic potential (Erf(r/rc)/r) - not available for DFTB.

-   `S-WAVE` Using fast Gaussian expansion of the s-wave electrostatic potential

-   `POINT_CHARGE` Using quantum mechanics derived point charges interacting with MM charges


**Mentions:** ⭐[QM/MM with Built-in Force Field](https://manual.cp2k.org/cp2k-2026_2-branch/methods/qm_mm/builtin.html)

Selects the QM-MM coupling model used for the electrostatic interaction. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L104)\]

### INITIAL\_TRANSLATION\_VECTOR*: real\[3\]* *\= 0.00000000E+000 0.00000000E+000 0.00000000E+000*

**Usage:** *initial\_translation\_vector*

This keyword specify the initial translation vector to be applied to the system. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L213)\]

### MM\_POTENTIAL\_FILE\_NAME*: string* *\= MM\_POTENTIAL*

**Usage:** *MM\_POTENTIAL\_FILE\_NAME {filename}*

Name of the file containing the potential expansion in gaussians. See the USE\_GEEP\_LIB keyword. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L120)\]

### NOCOMPATIBILITY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *nocompatibility LOGICAL*

This keyword disables the compatibility of QM/MM potential between CPMD and CP2K implementations. The compatibility is achieved using an MM potential of the form: Erf\[x/rc\]/x + (1/rc -2/(pi^1/2\*rc))\*Exp\[-(x/rc)^2\]. This keyword has effect only selecting GAUSS E\_COUPLING type. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L138)\]

### PARALLEL\_SCHEME*: enum* *\= ATOM*

**Usage:** *parallel\_scheme (ATOM|GRID)*

**Valid values:**

-   `ATOM` parallelizes on atoms. grids replicated. Replication of the grids can be quite expensive memory wise if running on a system with limited memory per core. The grid option may be preferred in this case.

-   `GRID` parallelizes on grid slices. atoms replicated.


Chooses the parallel\_scheme for the long range Potential \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L168)\]

### SPHERICAL\_CUTOFF*: real\[2\]* *\= \-5.29177209E-001 0.00000000E+000 \[angstrom\]*

**Usage:** *SPHERICAL\_CUTOFF*

Set the spherical cutoff for the QMMM electrostatic interaction. This acts like a charge multiplicative factor dependent on cutoff. For MM atoms farther than the SPHERICAL\_CUTOFF(1) their charge is zero. The switch is performed with a smooth function: 0.5\*(1-TANH((r-\[SPH\_CUT(1)-20\*SPH\_CUT(2)\])/(SPH\_CUT(2)))). Two values are required: the first one is the distance cutoff. The second one controls the stiffness of the smoothing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L156)\]

### USE\_GEEP\_LIB*: integer* *\= 0*

**Usage:** *use\_geep\_lib INTEGER*

This keyword enables the use of the internal GEEP library to generate the gaussian expansion of the MM potential. Using this keyword there’s no need to provide the MM\_POTENTIAL\_FILENAME. It expects a number from 2 to 15 (the number of gaussian functions to be used in the expansion. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qmmm.F#L128)\]
