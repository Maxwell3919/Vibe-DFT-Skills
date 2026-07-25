# CP2K official manual snapshot: md-thermostat

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT.html
- Raw SHA-256: 64bf18c2ecdfb98ac34bc2082c01e823350bc6c5e1cc5a76c1a76d5f9cca6688
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# THERMOSTAT

Specify thermostat type and parameters controlling the thermostat. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_thermostats.F#L228)\]

Subsections

-   [AD\_LANGEVIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/AD_LANGEVIN.html)
-   [CSVR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/CSVR.html)
-   [DEFINE\_REGION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/DEFINE_REGION.html)
-   [GLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/GLE.html)
-   [NOSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/NOSE.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT/PRINT.html)

## Keywords

-   [REGION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT.html#CP2K_INPUT.MOTION.MD.THERMOSTAT.REGION "CP2K_INPUT.MOTION.MD.THERMOSTAT.REGION")

-   **[TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT.html#CP2K_INPUT.MOTION.MD.THERMOSTAT.TYPE "CP2K_INPUT.MOTION.MD.THERMOSTAT.TYPE")**


## Keyword descriptions

### REGION*: enum* *\= GLOBAL*

**Usage:** *REGION (GLOBAL|MOLECULE|MASSIVE|DEFINED|THERMAL|NONE)*

**Valid values:**

-   `GLOBAL` Apply one thermostat to the whole system (default)

-   `MOLECULE` Apply one thermostat to each molecule kind

-   `MASSIVE` Apply one thermostat to each degree of freedom

-   `DEFINED` Apply one thermostat to each defined region from THERMOSTAT/DEFINE\_REGION

-   `THERMAL` Apply one thermostat to each defined region from THERMAL\_REGION/DEFINE\_REGION

-   `NONE` No thermostat is applied


Determines the region each thermostat is attached to. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_thermostats.F#L248)\]

### TYPE*: enum* *\= NOSE*

**Usage:** *TYPE NOSE*

**Valid values:**

-   `NOSE` Uses the Nose-Hoover thermostat.

-   `CSVR` Uses the canonical sampling through velocity rescaling.

-   `GLE` Uses GLE thermostat

-   `AD_LANGEVIN` Uses adaptive-Langevin thermostat


**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Specify the thermostat used for the constant temperature ensembles. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_thermostats.F#L234)\]
