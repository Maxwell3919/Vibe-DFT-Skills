# CP2K official manual snapshot: ext-restart

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html
- Raw SHA-256: 791a924502301466166227e3c90cb33e497727d6e6dbfbd873e544a7676301d2
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# EXT\_RESTART

Section for external restart, specifies an external input file where to take positions, etc. By default they are all set to TRUE \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L441)\]

## Keywords

-   [BINARY\_RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.BINARY_RESTART_FILE_NAME "CP2K_INPUT.EXT_RESTART.BINARY_RESTART_FILE_NAME")

-   [CUSTOM\_PATH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.CUSTOM_PATH "CP2K_INPUT.EXT_RESTART.CUSTOM_PATH")

-   [RESTART\_AVERAGES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_AVERAGES "CP2K_INPUT.EXT_RESTART.RESTART_AVERAGES")

-   [RESTART\_BAND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_BAND "CP2K_INPUT.EXT_RESTART.RESTART_BAND")

-   [RESTART\_BAROSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_BAROSTAT "CP2K_INPUT.EXT_RESTART.RESTART_BAROSTAT")

-   [RESTART\_BAROSTAT\_THERMOSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_BAROSTAT_THERMOSTAT "CP2K_INPUT.EXT_RESTART.RESTART_BAROSTAT_THERMOSTAT")

-   [RESTART\_BSSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_BSSE "CP2K_INPUT.EXT_RESTART.RESTART_BSSE")

-   [RESTART\_CELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_CELL "CP2K_INPUT.EXT_RESTART.RESTART_CELL")

-   [RESTART\_CONSTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_CONSTRAINT "CP2K_INPUT.EXT_RESTART.RESTART_CONSTRAINT")

-   [RESTART\_CORE\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_CORE_POS "CP2K_INPUT.EXT_RESTART.RESTART_CORE_POS")

-   [RESTART\_CORE\_VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_CORE_VELOCITY "CP2K_INPUT.EXT_RESTART.RESTART_CORE_VELOCITY")

-   [RESTART\_COUNTERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_COUNTERS "CP2K_INPUT.EXT_RESTART.RESTART_COUNTERS")

-   [RESTART\_DEFAULT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_DEFAULT "CP2K_INPUT.EXT_RESTART.RESTART_DEFAULT")

-   [RESTART\_DIMER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_DIMER "CP2K_INPUT.EXT_RESTART.RESTART_DIMER")

-   [RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_FILE_NAME "CP2K_INPUT.EXT_RESTART.RESTART_FILE_NAME")

-   [RESTART\_HELIUM\_AVERAGES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_AVERAGES "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_AVERAGES")

-   [RESTART\_HELIUM\_DENSITIES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_DENSITIES "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_DENSITIES")

-   [RESTART\_HELIUM\_FORCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_FORCE "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_FORCE")

-   [RESTART\_HELIUM\_PERMUTATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_PERMUTATION "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_PERMUTATION")

-   [RESTART\_HELIUM\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_POS "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_POS")

-   [RESTART\_HELIUM\_RNG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_RNG "CP2K_INPUT.EXT_RESTART.RESTART_HELIUM_RNG")

-   [RESTART\_METADYNAMICS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_METADYNAMICS "CP2K_INPUT.EXT_RESTART.RESTART_METADYNAMICS")

-   [RESTART\_OPTIMIZE\_INPUT\_VARIABLES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_OPTIMIZE_INPUT_VARIABLES "CP2K_INPUT.EXT_RESTART.RESTART_OPTIMIZE_INPUT_VARIABLES")

-   [RESTART\_PINT\_GLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_PINT_GLE "CP2K_INPUT.EXT_RESTART.RESTART_PINT_GLE")

-   [RESTART\_PINT\_NOSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_PINT_NOSE "CP2K_INPUT.EXT_RESTART.RESTART_PINT_NOSE")

-   [RESTART\_PINT\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_PINT_POS "CP2K_INPUT.EXT_RESTART.RESTART_PINT_POS")

-   [RESTART\_PINT\_VEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_PINT_VEL "CP2K_INPUT.EXT_RESTART.RESTART_PINT_VEL")

-   [RESTART\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_POS "CP2K_INPUT.EXT_RESTART.RESTART_POS")

-   [RESTART\_QMMM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_QMMM "CP2K_INPUT.EXT_RESTART.RESTART_QMMM")

-   [RESTART\_RANDOMG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_RANDOMG "CP2K_INPUT.EXT_RESTART.RESTART_RANDOMG")

-   [RESTART\_RTP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_RTP "CP2K_INPUT.EXT_RESTART.RESTART_RTP")

-   [RESTART\_SHELL\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_SHELL_POS "CP2K_INPUT.EXT_RESTART.RESTART_SHELL_POS")

-   [RESTART\_SHELL\_THERMOSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_SHELL_THERMOSTAT "CP2K_INPUT.EXT_RESTART.RESTART_SHELL_THERMOSTAT")

-   [RESTART\_SHELL\_VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_SHELL_VELOCITY "CP2K_INPUT.EXT_RESTART.RESTART_SHELL_VELOCITY")

-   [RESTART\_TEMPERATURE\_ANNEALING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_TEMPERATURE_ANNEALING "CP2K_INPUT.EXT_RESTART.RESTART_TEMPERATURE_ANNEALING")

-   [RESTART\_THERMOSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_THERMOSTAT "CP2K_INPUT.EXT_RESTART.RESTART_THERMOSTAT")

-   [RESTART\_VEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_VEL "CP2K_INPUT.EXT_RESTART.RESTART_VEL")

-   [RESTART\_WALKERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html#CP2K_INPUT.EXT_RESTART.RESTART_WALKERS "CP2K_INPUT.EXT_RESTART.RESTART_WALKERS")


## Keyword descriptions

### BINARY\_RESTART\_FILE\_NAME*: string*

**Aliases:** BINARY\_RESTART\_FILE

Specifies the name of an additional restart file from which selected input sections are read in binary format (see SPLIT\_RESTART\_FILE). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L456)\]

### CUSTOM\_PATH*: string*

**Keyword can be repeated.**

Restarts the given path from the EXTERNAL file. Allows a major flexibility for restarts. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L601)\]

### RESTART\_AVERAGES*: logical*

**Lone keyword:** `T`

Restarts information for AVERAGES. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L591)\]

### RESTART\_BAND*: logical*

**Lone keyword:** `T`

Restarts positions and velocities of the Band. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L564)\]

### RESTART\_BAROSTAT*: logical*

**Lone keyword:** `T`

Restarts the barostat from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L520)\]

### RESTART\_BAROSTAT\_THERMOSTAT*: logical*

**Lone keyword:** `T`

Restarts the barostat thermostat from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L525)\]

### RESTART\_BSSE*: logical*

**Lone keyword:** `T`

Restarts information for BSSE calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L581)\]

### RESTART\_CELL*: logical*

**Lone keyword:** `T`

Restarts the cell (and cell\_ref) from the EXTERNAL file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L546)\]

### RESTART\_CONSTRAINT*: logical*

**Lone keyword:** `T`

Restarts constraint section. It’s necessary when doing restraint calculation to have a perfect energy conservation. For constraints only its use is optional. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L574)\]

### RESTART\_CORE\_POS*: logical*

**Lone keyword:** `T`

Takes the positions of the cores from the external file (only if shell-model) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L499)\]

### RESTART\_CORE\_VELOCITY*: logical*

**Lone keyword:** `T`

Takes the velocities of the shells from the external file (only if shell-model) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L515)\]

### RESTART\_COUNTERS*: logical*

**Lone keyword:** `T`

Restarts the counters in MD schemes and optimization STEP \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L473)\]

### RESTART\_DEFAULT*: logical* *\= T*

This keyword controls the default value for all possible restartable keywords, unless explicitly defined. For example setting this keyword to .FALSE. does not restart any quantity. If, at the same time, one keyword is set to .TRUE. only that quantity will be restarted. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L465)\]

### RESTART\_DIMER*: logical*

**Lone keyword:** `T`

Restarts information for DIMER geometry optimizations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L586)\]

### RESTART\_FILE\_NAME*: string*

**Aliases:** EXTERNAL\_FILE

Specifies the name of restart file (or any other input file) to be read. Only fields relevant to a restart will be used (unless switched off with the keywords in this section) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L448)\]

### RESTART\_HELIUM\_AVERAGES*: logical* *\= F*

**Lone keyword:** `T`

Restarts average properties from PINT%HELIUM%AVERAGES. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L656)\]

### RESTART\_HELIUM\_DENSITIES*: logical* *\= F*

**Lone keyword:** `T`

Restarts helium density distributions from PINT%HELIUM%RHO. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L650)\]

### RESTART\_HELIUM\_FORCE*: logical*

**Lone keyword:** `T`

Restart helium forces exerted on the solute from PINT%HELIUM%FORCE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L640)\]

### RESTART\_HELIUM\_PERMUTATION*: logical*

**Lone keyword:** `T`

Restart helium permutation state from PINT%HELIUM%PERM. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L635)\]

### RESTART\_HELIUM\_POS*: logical*

**Lone keyword:** `T`

Restart helium positions from PINT%HELIUM%COORD. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L630)\]

### RESTART\_HELIUM\_RNG*: logical*

**Lone keyword:** `T`

Restarts helium random number generators from PINT%HELIUM%RNG\_STATE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L645)\]

### RESTART\_METADYNAMICS*: logical*

**Lone keyword:** `T`

Restarts hills from a previous metadynamics run from the EXTERNAL file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L552)\]

### RESTART\_OPTIMIZE\_INPUT\_VARIABLES*: logical*

**Lone keyword:** `T`

Restart with the optimize input variables \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L504)\]

### RESTART\_PINT\_GLE*: logical*

**Lone keyword:** `T`

Restart GLE thermostat for beads from PINT%GLE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L623)\]

### RESTART\_PINT\_NOSE*: logical*

**Lone keyword:** `T`

Restart Nose thermostat for beads from PINT%NOSE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L618)\]

### RESTART\_PINT\_POS*: logical*

**Lone keyword:** `T`

Restart bead positions from PINT%BEADS%COORD. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L608)\]

### RESTART\_PINT\_VEL*: logical*

**Lone keyword:** `T`

Restart bead velocities from PINT%BEADS%VELOCITY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L613)\]

### RESTART\_POS*: logical*

**Lone keyword:** `T`

Takes the positions from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L478)\]

### RESTART\_QMMM*: logical*

**Lone keyword:** `T`

Restarts the following specific QMMM info: translation vectors. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L569)\]

### RESTART\_RANDOMG*: logical*

**Lone keyword:** `T`

Restarts the random number generator from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L488)\]

### RESTART\_RTP*: logical*

**Lone keyword:** `T`

Restarts information for REAL TIME PROPAGATION and EHRENFEST DYNAMICS. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L596)\]

### RESTART\_SHELL\_POS*: logical*

**Lone keyword:** `T`

Takes the positions of the shells from the external file (only if shell-model) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L494)\]

### RESTART\_SHELL\_THERMOSTAT*: logical*

**Lone keyword:** `T`

Restarts the shell thermostat from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L530)\]

### RESTART\_SHELL\_VELOCITY*: logical*

**Lone keyword:** `T`

Takes the velocities of the shells from the external file (only if shell-model) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L510)\]

### RESTART\_TEMPERATURE\_ANNEALING*: logical* *\= F*

**Lone keyword:** `T`

Restarts external temperature when using TEMPERATURE\_ANNEALING. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L541)\]

### RESTART\_THERMOSTAT*: logical*

**Lone keyword:** `T`

Restarts the nose thermostats of the particles from the EXTERNAL file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L535)\]

### RESTART\_VEL*: logical*

**Lone keyword:** `T`

Takes the velocities from the external file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L483)\]

### RESTART\_WALKERS*: logical*

**Lone keyword:** `T`

Restarts walkers informations from a previous metadynamics run from the EXTERNAL file \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/start/input_cp2k.F#L558)\]
