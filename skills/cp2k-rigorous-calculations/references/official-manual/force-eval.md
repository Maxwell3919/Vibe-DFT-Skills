# CP2K official manual snapshot: force-eval

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL.html
- Raw SHA-256: 13342298309800dffc41de24bad9bdf810d1d931cc072eb3ad556069f65bcd58
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# FORCE\_EVAL

**Section can be repeated.**

parameters needed to calculate energy and forces and describe the system you want to analyze. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_force_eval.F#L75)\]

Subsections

-   [BSSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/BSSE.html)
-   [DFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html)
-   [EIP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/EIP.html)
-   [EMBED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/EMBED.html)
-   [EXTERNAL\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/EXTERNAL_POTENTIAL.html)
-   [MIXED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/MIXED.html)
-   [MM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/MM.html)
-   [NNP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/NNP.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PRINT.html)
-   [PROPERTIES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES.html)
-   [PW\_DFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PW_DFT.html)
-   [QMMM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html)
-   [RESCALE\_FORCES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/RESCALE_FORCES.html)
-   [SUBSYS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS.html)

## Keywords

-   **[METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL.html#CP2K_INPUT.FORCE_EVAL.METHOD "CP2K_INPUT.FORCE_EVAL.METHOD")**

-   **[STRESS\_TENSOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL.html#CP2K_INPUT.FORCE_EVAL.STRESS_TENSOR "CP2K_INPUT.FORCE_EVAL.STRESS_TENSOR")**


## Keyword descriptions

### METHOD*: enum* *\= QS*

**Usage:** *METHOD*

**Valid values:**

-   `QS` Alias for QUICKSTEP

-   `SIRIUS` PW DFT using the SIRIUS library

-   `FIST` Molecular Mechanics

-   `QMMM` Hybrid quantum classical

-   `EIP` Empirical Interatomic Potential

-   `QUICKSTEP` Electronic structure methods in the Quickstep module, including GPW and GAPW DFT.

-   `NNP` Neural Network Potentials

-   `MIXED` Use a combination of two of the above

-   `EMBED` Perform an embedded calculation

-   `IPI` Receive forces from an i-PI client


**Mentions:** ⭐[Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html)

Selects the method used by this FORCE\_EVAL section to compute energies, forces, and related properties. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_force_eval.F#L82)\]

### STRESS\_TENSOR*: enum* *\= NONE*

**Usage:** *stress\_tensor (NONE|ANALYTICAL|NUMERICAL|DIAGONAL\_ANA|DIAGONAL\_NUM)*

**Valid values:**

-   `NONE` Do not compute stress tensor

-   `ANALYTICAL` Compute the stress tensor analytically (if available).

-   `NUMERICAL` Compute the stress tensor numerically.

-   `DIAGONAL_ANALYTICAL` Compute the diagonal part only of the stress tensor analytically (if available).

-   `DIAGONAL_NUMERICAL` Compute the diagonal part only of the stress tensor numerically


**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Controls the calculation of the stress tensor. The combinations defined below are not implemented for all methods. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_force_eval.F#L111)\]
