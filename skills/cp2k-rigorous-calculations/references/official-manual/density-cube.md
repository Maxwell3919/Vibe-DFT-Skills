# CP2K official manual snapshot: density-cube

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html
- Raw SHA-256: 14be00741ca24e39694caa174c9d862cdf1c744c2af14c89eaaa34409281f88a
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# E\_DENSITY\_CUBE

Controls the printing of cube files with the electronic density and, for LSD calculations, the spin density. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2597)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.ADD_LAST")

-   [APPEND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.APPEND "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.APPEND")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.COMMON_ITERATION_LEVELS")

-   [DENSITY\_INCLUDE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.DENSITY_INCLUDE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.DENSITY_INCLUDE")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.FILENAME")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.LOG_PRINT_KEY")

-   [NGAUSS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.NGAUSS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.NGAUSS")

-   [STRIDE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.STRIDE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.STRIDE")

-   [XRD\_INTERFACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.XRD_INTERFACE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.XRD_INTERFACE")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.E_DENSITY_CUBE.__CONTROL_VAL")


## Keyword descriptions

### SECTION\_PARAMETERS*: enum* *\= HIGH*

**Lone keyword:** `SILENT`

**Usage:** *silent*

**Valid values:**

-   `ON`

-   `OFF`

-   `SILENT`

-   `LOW`

-   `MEDIUM`

-   `HIGH`

-   `DEBUG`


Level starting at which this property is printed \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L203)\]

### ADD\_LAST*: enum* *\= NO*

**Usage:** *ADD\_LAST (NO|NUMERIC|SYMBOLIC)*

**Valid values:**

-   `NO` Do not mark last iteration specifically

-   `NUMERIC` Mark last iteration with its iteration number

-   `SYMBOLIC` Mark last iteration with lowercase letter l


If the last iteration should be added, and if it should be marked symbolically (with lowercase letter l) or with the iteration number. Not every iteration level is able to identify the last iteration early enough to be able to output. When this keyword is activated all iteration levels are checked for the last iteration step. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L262)\]

### APPEND*: logical* *\= F*

**Lone keyword:** `T`

append the cube files when they already exist \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L869)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 0*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### DENSITY\_INCLUDE*: enum* *\= TOTAL\_HARD\_APPROX*

**Usage:** *DENSITY\_INCLUDE TOTAL\_HARD\_APPROX*

**Valid values:**

-   `TOTAL_HARD_APPROX` Print (hard+soft) density where the hard components shape is approximated

-   `TOTAL_DENSITY` Print (hard+soft) density. Only has an effect if PAW atoms are present. NOTE: The total in real space might exhibit unphysical features like spikes due to the finite and thus truncated g vector

-   `SOFT_DENSITY` Print only the soft density


Which parts of the density to include. In GAPW the electronic density is divided into a hard and a soft component, and the default (TOTAL\_HARD\_APPROX) is to approximate the hard density as a spherical gaussian and to print the smooth density accurately. This avoids potential artefacts originating from the hard density. If the TOTAL\_DENSITY keyword is used the hard density will be computed more accurately but may introduce non-physical features. The SOFT\_DENSITY keyword will lead to only the soft density being printed. In GPW these options have no effect and the cube file will only contain the valence electron density. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2611)\]

### FILENAME*: string*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### NGAUSS*: integer* *\= 12*

**Usage:** *NGAUSS 10*

Number of Gaussian functions used in the expansion of atomic (core) density \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L886)\]

### STRIDE*: integer\[ \]* *\= 2 2 2*

**Usage:** *STRIDE 2 2 2*

The stride (X,Y,Z) used to write the cube file (larger values result in smaller cube files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2601)\]

### XRD\_INTERFACE*: logical* *\= F*

**Lone keyword:** `T`

It activates the print out of exponents and coefficients for the Gaussian expansion of the core densities, based on atom calculations for each kind. The resulting core dansities are needed to compute the form factors. If GAPW the local densities are also given in terms of a Gaussian expansion, by fitting the difference between local-fhard and local-soft density for each atom. In this case the keyword SOFT\_DENSITY is enabled. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L875)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
