# CP2K official manual snapshot: elf-cube

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html
- Raw SHA-256: d23c739afbd98a25058ee9c2f0689ea85de3038963f9f7d910f8f51fb98dcad0
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# ELF\_CUBE

Controls printing of cube files with the electron localization function (ELF). Note that the value of ELF is defined between 0 and 1: Pauli kinetic energy density normalized by the kinetic energy density of a uniform el. gas of same density. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2658)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.ADD_LAST")

-   [APPEND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.APPEND "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.APPEND")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.COMMON_ITERATION_LEVELS")

-   [DENSITY\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.DENSITY_CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.DENSITY_CUTOFF")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.FILENAME")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.LOG_PRINT_KEY")

-   [STRIDE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.STRIDE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.STRIDE")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.ELF_CUBE.__CONTROL_VAL")


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

append the cube files when they already exist \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L1107)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 0*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### DENSITY\_CUTOFF*: real* *\= 1.00000000E-010*

**Usage:** *density\_cutoff 0.0001*

\[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2672)\]

### FILENAME*: string*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### STRIDE*: integer\[ \]* *\= 2 2 2*

**Usage:** *STRIDE 2 2 2*

The stride (X,Y,Z) used to write the file (larger values result in smaller files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2665)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
