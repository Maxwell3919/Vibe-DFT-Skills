# CP2K official manual snapshot: hirshfeld

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html
- Raw SHA-256: bfc28ed4f064c51177b9a88fcf329823057af48dc6a34451e0547cdfb01cfef4
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# HIRSHFELD

Controls the printing of the Hirshfeld (spin) population analysis \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1374)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.ADD_LAST")

-   [ATOMIC\_RADII](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.ATOMIC_RADII "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.ATOMIC_RADII")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.COMMON_ITERATION_LEVELS")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.FILENAME")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.LOG_PRINT_KEY")

-   [REFERENCE\_CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.REFERENCE_CHARGE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.REFERENCE_CHARGE")

-   [SELF\_CONSISTENT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SELF_CONSISTENT "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SELF_CONSISTENT")

-   [SHAPE\_FUNCTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SHAPE_FUNCTION "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.SHAPE_FUNCTION")

-   [USER\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.USER_RADIUS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.USER_RADIUS")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.HIRSHFELD.__CONTROL_VAL")


## Keyword descriptions

### SECTION\_PARAMETERS*: enum* *\= MEDIUM*

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

### ATOMIC\_RADII*: real\[ \]* *\= \[angstrom\]*

**Usage:** *ATOMIC\_RADII {real} {real} {real}*

Defines custom radii to setup the spherical Gaussians. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1411)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 1*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### FILENAME*: string* *\= \_\_STD\_OUT\_\_*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### REFERENCE\_CHARGE*: enum* *\= ATOMIC*

**Usage:** *REFERENCE\_CHARGE {Atomic,Mulliken}*

**Valid values:**

-   `ATOMIC` Use atomic core charges

-   `MULLIKEN` Calculate Mulliken charges


Charge of atomic partitioning function for Hirshfeld method. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1395)\]

### SELF\_CONSISTENT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SELF\_CONSISTENT yes*

Calculate charges from the Hirscheld-I (self\_consistent) method. This scales only the full shape function, not the added charge as in the original scheme. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1378)\]

### SHAPE\_FUNCTION*: enum* *\= GAUSSIAN*

**Usage:** *SHAPE\_FUNCTION {Gaussian,Density}*

**Valid values:**

-   `GAUSSIAN` Single Gaussian with Colvalent radius

-   `DENSITY` Atomic density expanded in multiple Gaussians


Type of shape function used for Hirshfeld partitioning. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1385)\]

### USER\_RADIUS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *USER\_RADIUS yes*

Use user defined radii to generate Gaussians. These radii are defined by the keyword ATOMIC\_RADII \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1404)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
