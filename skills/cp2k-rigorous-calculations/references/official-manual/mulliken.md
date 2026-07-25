# CP2K official manual snapshot: mulliken

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html
- Raw SHA-256: 4ce30f5f82d0e6097dfe56488ec9d469e487d24ca3ccd3b471a873aea913b745
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# MULLIKEN

Controls the printing of the Mulliken (spin) population analysis \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1313)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.ADD_LAST")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.COMMON_ITERATION_LEVELS")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.FILENAME")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.LOG_PRINT_KEY")

-   [PRINT\_ALL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.PRINT_ALL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.PRINT_ALL")

-   [PRINT\_GOP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.PRINT_GOP "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.PRINT_GOP")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MULLIKEN.__CONTROL_VAL")


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

### PRINT\_ALL*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *PRINT\_ALL yes*

Print all information including the full net AO and overlap population matrix \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1330)\]

### PRINT\_GOP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *PRINT\_GOP yes*

Print the gross orbital populations (GOP) in addition to the gross atomic populations (GAP) and net charges \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1318)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
