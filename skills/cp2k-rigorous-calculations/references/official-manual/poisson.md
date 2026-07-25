# CP2K official manual snapshot: poisson

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON.html
- Raw SHA-256: 859bf837154f3bd382984e7fbc4aa73665b0f59991f1bfc611b3456de67de401
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# POISSON

Controls the Poisson solver and electrostatic boundary conditions used by DFT. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_poisson.F#L110)\]

Subsections

-   [EWALD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/EWALD.html)
-   [IMPLICIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/IMPLICIT.html)
-   [MT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/MT.html)
-   [MULTIPOLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/MULTIPOLE.html)
-   [WAVELET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/WAVELET.html)

## Keywords

-   [PERIODIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON.html#CP2K_INPUT.FORCE_EVAL.DFT.POISSON.PERIODIC "CP2K_INPUT.FORCE_EVAL.DFT.POISSON.PERIODIC")

-   [POISSON\_SOLVER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON.html#CP2K_INPUT.FORCE_EVAL.DFT.POISSON.POISSON_SOLVER "CP2K_INPUT.FORCE_EVAL.DFT.POISSON.POISSON_SOLVER")


## Keyword descriptions

### PERIODIC*: enum* *\= XYZ*

**Usage:** *PERIODIC (x|y|z|xy|xz|yz|xyz|none)*

**Valid values:**

-   `X`

-   `Y`

-   `Z`

-   `XY`

-   `XZ`

-   `YZ`

-   `XYZ`

-   `NONE`


Specifies the directions in which periodic boundary conditions apply to electrostatics. See the CELL section for the periodicity used by geometry and pair lists; the settings are usually the same. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_poisson.F#L140)\]

### POISSON\_SOLVER*: enum* *\= PERIODIC*

**Aliases:** POISSON ,PSOLVER

**Usage:** *POISSON\_SOLVER char*

**Valid values:**

-   `PERIODIC` PERIODIC is only available for fully (3D) periodic systems.

-   `ANALYTIC` ANALYTIC is available for 0D, 1D and 2D periodic solutions using analytical green functions in the g space (slow convergence).

-   `MT` MT (Martyna Tuckermann) decoupling that interacts only with the nearest neighbor. Beware results are completely wrong if the cell is smaller than twice the cluster size (with electronic density). Available for 0D and 2D systems.

-   `MULTIPOLE` MULTIPOLE uses a scheme that fits the total charge with one gaussian per atom. Available only for cluster (0D) systems.

-   `WAVELET` WAVELET allows for 0D, 2D and 3D systems. For 2D systems all PERIODIC XY, XZ and YZ combinations are accepted. It does not require very large unit cells, only that the density goes to zero on the faces of the cell. The use of PREFERRED\_FFT\_LIBRARY FFTSG is required.

-   `IMPLICIT` IMPLICIT allows for 0D, 1D, 2D and 3D systems.


**References:** [Blöchl1995](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#blochl1995), [Martyna1999](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#martyna1999), [Genovese2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#genovese2006), [Genovese2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#genovese2007)

Specify which kind of solver to use to solve the Poisson equation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_poisson.F#L115)\]
