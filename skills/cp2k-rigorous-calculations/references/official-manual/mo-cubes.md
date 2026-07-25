# CP2K official manual snapshot: mo-cubes

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html
- Raw SHA-256: 474a5074befe69d53a7d245866f31555374de802e8869d00e9fe6f19882ebbd6
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# MO\_CUBES

Controls the printing of the molecular orbitals (MOs) as cube files. It can be used during a Real Time calculation to print the MOs. In this case, the density corresponding to the time dependent MO is printed instead of the wave-function. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2528)\]

Subsections

-   [EACH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES/EACH.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.SECTION_PARAMETERS")

-   [ADD\_LAST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.ADD_LAST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.ADD_LAST")

-   [APPEND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.APPEND "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.APPEND")

-   [COMMON\_ITERATION\_LEVELS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.COMMON_ITERATION_LEVELS "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.COMMON_ITERATION_LEVELS")

-   [FILENAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.FILENAME "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.FILENAME")

-   **[HOMO\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.HOMO_LIST "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.HOMO_LIST")**

-   [LOG\_PRINT\_KEY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.LOG_PRINT_KEY "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.LOG_PRINT_KEY")

-   **[MAX\_FILE\_SIZE\_MB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.MAX_FILE_SIZE_MB "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.MAX_FILE_SIZE_MB")**

-   **[NHOMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.NHOMO "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.NHOMO")**

-   **[NLUMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.NLUMO "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.NLUMO")**

-   **[STRIDE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.STRIDE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.STRIDE")**

-   **[WRITE\_CUBE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.WRITE_CUBE "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.WRITE_CUBE")**

-   [\_\_CONTROL\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html#CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.__CONTROL_VAL "CP2K_INPUT.FORCE_EVAL.DFT.PRINT.MO_CUBES.__CONTROL_VAL")


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

append the cube files when they already exist \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L704)\]

### COMMON\_ITERATION\_LEVELS*: integer* *\= 0*

**Usage:** *COMMON\_ITERATION\_LEVELS*

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L281)\]

### FILENAME*: string*

**Usage:** *FILENAME ./filename*

controls part of the filename for output. use \_\_STD\_OUT\_\_ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L292)\]

### HOMO\_LIST*: integer\[ \]*

**Keyword can be repeated.**

**Usage:** *HOMO\_LIST {integer} {integer} .. {integer}*

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

If the printkey is activated controls the index of homos dumped as openPMD, eigenvalues are always all dumped. It overrides nhomo. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2574)\]

### LOG\_PRINT\_KEY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LOG\_PRINT\_KEY*

This keywords enables the logger for the print\_key (a message is printed on screen everytime data, controlled by this print\_key, are written) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L308)\]

### MAX\_FILE\_SIZE\_MB*: real* *\= 0.00000000E+000*

**Usage:** *MAX\_FILE\_SIZE\_MB 1.5*

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

Limits the size of the cube file by choosing a suitable stride. Zero means no limit. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L709)\]

### NHOMO*: integer* *\= 1*

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

If the printkey is activated controls the number of homos that dumped as cube (-1=all), eigenvalues are always all dumped \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2564)\]

### NLUMO*: integer* *\= 0*

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

If the printkey is activated controls the number of lumos that are printed and dumped as cube (-1=all) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2556)\]

### STRIDE*: integer\[ \]* *\= 2 2 2*

**Usage:** *STRIDE 1 1 1*

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

The stride (X,Y,Z) used to write the cube file (larger values result in smaller cube files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2537)\]

### WRITE\_CUBE*: logical* *\= T*

**Lone keyword:** `T`

**Mentions:** ⭐[Molecular orbitals output](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/molecular_orbitals.html)

If the MO cube file should be written. If false, the eigenvalues are still computed. Can also be useful in combination with STM calculations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_print_dft.F#L2547)\]

### \_\_CONTROL\_VAL*: integer* *\= 8*

hidden parameter that controls storage, printing,… of the print\_key \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input/cp_output_handling.F#L214)\]
