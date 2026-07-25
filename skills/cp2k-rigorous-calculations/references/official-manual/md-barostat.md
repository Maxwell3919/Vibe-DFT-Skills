# CP2K official manual snapshot: md-barostat

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html
- Raw SHA-256: d5439ccd02799cb75b43895eda8ed36b95aebbdf2eec2629b8151117ee4cdc83
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# BAROSTAT

Parameters of barostat. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L63)\]

Subsections

-   [MASS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT/MASS.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT/PRINT.html)
-   [THERMOSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT/THERMOSTAT.html)
-   [VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT/VELOCITY.html)

## Keywords

-   **[PRESSURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html#CP2K_INPUT.MOTION.MD.BAROSTAT.PRESSURE "CP2K_INPUT.MOTION.MD.BAROSTAT.PRESSURE")**

-   [TEMPERATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html#CP2K_INPUT.MOTION.MD.BAROSTAT.TEMPERATURE "CP2K_INPUT.MOTION.MD.BAROSTAT.TEMPERATURE")

-   [TEMP\_TOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html#CP2K_INPUT.MOTION.MD.BAROSTAT.TEMP_TOL "CP2K_INPUT.MOTION.MD.BAROSTAT.TEMP_TOL")

-   **[TIMECON](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html#CP2K_INPUT.MOTION.MD.BAROSTAT.TIMECON "CP2K_INPUT.MOTION.MD.BAROSTAT.TIMECON")**

-   **[VIRIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html#CP2K_INPUT.MOTION.MD.BAROSTAT.VIRIAL "CP2K_INPUT.MOTION.MD.BAROSTAT.VIRIAL")**


## Keyword descriptions

### PRESSURE*: real* *\= 0.00000000E+000 \[bar\]*

**Usage:** *PRESSURE real*

**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Initial pressure \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L68)\]

### TEMPERATURE*: real* *\= \[K\]*

**Usage:** *TEMPERATURE real*

Barostat initial temperature. If not set, the ensemble temperature is used instead. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L83)\]

### TEMP\_TOL*: real* *\= 0.00000000E+000 \[K\]*

**Usage:** *TEMP\_TOL real*

Maximum oscillation of the Barostat temperature imposed by rescaling. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L90)\]

### TIMECON*: real* *\= 1.00000000E+003 \[fs\]*

**Usage:** *TIMECON real*

**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Barostat time constant \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L75)\]

### VIRIAL*: enum* *\= XYZ*

**Usage:** *VIRIAL (XYZ | X | Y | Z | XY| XZ | YZ)*

**Valid values:**

-   `XYZ`

-   `X`

-   `Y`

-   `Z`

-   `XY`

-   `XZ`

-   `YZ`


**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

For NPT\_F only: allows the screening of one or more components of the virial in order to relax the cell only along specific cartesian axis \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/thermostat/input_cp2k_barostats.F#L97)\]
