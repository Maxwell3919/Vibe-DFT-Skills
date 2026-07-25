# CP2K official manual snapshot: global-print

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html
- Raw SHA-256: 2bfc8e53be5f601dca3b4248c76b3efd98ff779201dfd48f9cb13a4f4a3dcda2
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# PRINT

controls the printing of physical and mathematical constants \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L595)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.SECTION_PARAMETERS "CP2K_INPUT.GLOBAL.PRINT.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.ADD_LAST "CP2K_INPUT.GLOBAL.PRINT.ADD_LAST")

-   [BASIC\_DATA\_TYPES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.BASIC_DATA_TYPES "CP2K_INPUT.GLOBAL.PRINT.BASIC_DATA_TYPES")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.COMMON_ITERATION_LEVELS "CP2K_INPUT.GLOBAL.PRINT.COMMON_ITERATION_LEVELS")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.FILENAME "CP2K_INPUT.GLOBAL.PRINT.FILENAME")

-   [GLOBAL\_GAUSSIAN\_RNG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.GLOBAL_GAUSSIAN_RNG "CP2K_INPUT.GLOBAL.PRINT.GLOBAL_GAUSSIAN_RNG")

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.LOG_PRINT_KEY "CP2K_INPUT.GLOBAL.PRINT.LOG_PRINT_KEY")

-   [PHYSCON](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.PHYSCON "CP2K_INPUT.GLOBAL.PRINT.PHYSCON")

-   [RNG\_CHECK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.RNG_CHECK "CP2K_INPUT.GLOBAL.PRINT.RNG_CHECK")

-   [RNG\_MATRICES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.RNG_MATRICES "CP2K_INPUT.GLOBAL.PRINT.RNG_MATRICES")

-   [SPHERICAL\_HARMONICS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.SPHERICAL_HARMONICS "CP2K_INPUT.GLOBAL.PRINT.SPHERICAL_HARMONICS")

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html#CP2K_INPUT.GLOBAL.PRINT.__CONTROL_VAL "CP2K_INPUT.GLOBAL.PRINT.__CONTROL_VAL")


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

### BASIC\_DATA\_TYPES*: logical* *\= F*

**Lone keyword:** `T`

Controls the printing of the basic data types. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L599)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 0*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### FILENAME*: string* *\= \_\_STD\_OUT\_\_*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### GLOBAL\_GAUSSIAN\_RNG*: logical* *\= F*

**Lone keyword:** `T`

Prints the initial status of the global Gaussian (pseudo)random number stream which is mostly used for the velocity initialization \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L627)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### PHYSCON*: logical* *\= T*

**Lone keyword:** `T`

if the printkey is active prints the physical constants \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L604)\]

### RNG\_CHECK*: logical* *\= F*

**Lone keyword:** `T`

Performs a check of the global (pseudo)random number generator (RNG) and prints the result \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L620)\]

### RNG\_MATRICES*: logical* *\= F*

**Lone keyword:** `T`

Prints the transformation matrices used by the random number generator \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L614)\]

### SPHERICAL\_HARMONICS*: integer* *\= \-1*

if the printkey is active prints the spherical harmonics \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L609)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
