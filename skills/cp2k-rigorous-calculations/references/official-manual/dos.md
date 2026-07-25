# CP2K official manual snapshot: dos

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html
- Raw SHA-256: 80df0e382ec8485e420117a2fe8227b3c5e660d4e8c87d1a070c1f023d484c55
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# DOS

Print density of states (DOS). Projected DOS output can be enabled with PDOS. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1181)\]

Subsections

-   [CURVE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS/CURVE.html)
-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS/EACH.html)
-   [LDOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS/LDOS.html)
-   [PDOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS/PDOS.html)
-   [R\_LDOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS/R_LDOS.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.ADD_LAST")

-   [APPEND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.APPEND "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.APPEND")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.COMMON_ITERATION_LEVELS")

-   **[DELTA\_E](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.DELTA_E "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.DELTA_E")**

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.FILENAME")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.LOG_PRINT_KEY")

-   [MP\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.MP_GRID "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.MP_GRID")

-   [NDIGITS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.NDIGITS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.NDIGITS")

-   **[NLUMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.NLUMO "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.NLUMO")**

-   [OUT\_EACH\_STATE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.OUT_EACH_STATE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.OUT_EACH_STATE")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.DOS.__CONTROL_VAL")


## Keyword descriptions

### SECTION\_PARAMETERS*: enum* *\= DEBUG*

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

**Usage:** *APPEND*

Append the DOS/PDOS obtained at different iterations to the output file. By default the file is overwritten \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2695)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 1*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### DELTA\_E*: real* *\= 1.00000000E-003*

**Usage:** *DELTA\_E 0.0005*

**Mentions:** ⭐[Density of States](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/dos.html)

Energy spacing of the DOS/PDOS output grid. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2708)\]

### FILENAME*: string*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### MP\_GRID*: integer\[3\]* *\= \-1*

**Usage:** *MP\_GRID {integer} {integer} {integer}*

Specify a Monkhorst-Pack grid with which to compute the density of states. Works only for a k-point calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1188)\]

### NDIGITS*: integer* *\= 6*

Specify the number of digits used to print DOS/PDOS values. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2702)\]

### NLUMO*: integer* *\= 0*

**Usage:** *NLUMO integer*

**Mentions:** ⭐[Density of States](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/dos.html)

Number of unoccupied orbitals to include in the DOS/PDOS (-1=all). For OT calculations, the requested virtual orbitals are generated after SCF using the OT eigensolver. For diagonalization calculations, SCF%ADDED\_MOS is increased if needed to make the requested unoccupied orbitals available. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2714)\]

### OUT\_EACH\_STATE*: integer* *\= \-1*

**Aliases:** OUT\_EACH\_MO

**Usage:** *OUT\_EACH\_STATE integer*

Output on the status of the calculation every OUT\_EACH\_MO states. If -1 no output \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2799)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
