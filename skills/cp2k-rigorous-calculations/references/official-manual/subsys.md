# CP2K official manual snapshot: subsys

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS.html
- Raw SHA-256: d4fb86bcbf43e2ce2b9046800fa01ea01869f99b866a96654478a61144a62278
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# SUBSYS

a subsystem: coordinates, topology, molecules and cell \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L328)\]

Subsections

-   [CELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/CELL.html)
-   [COLVAR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/COLVAR.html)
-   [COORD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/COORD.html)
-   [CORE\_COORD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/CORE_COORD.html)
-   [CORE\_VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/CORE_VELOCITY.html)
-   [KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html)
-   [MULTIPOLES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/MULTIPOLES.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/PRINT.html)
-   [RNG\_INIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/RNG_INIT.html)
-   [SHELL\_COORD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/SHELL_COORD.html)
-   [SHELL\_VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/SHELL_VELOCITY.html)
-   [TOPOLOGY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html)
-   [VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/VELOCITY.html)

## Keywords

-   [SEED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.SEED "CP2K_INPUT.FORCE_EVAL.SUBSYS.SEED")


## Keyword descriptions

### SEED*: integer\[ \]* *\= 12345*

**Usage:** *SEED {INTEGER} .. {INTEGER}*

Initial seed for the (pseudo)random number generator for the Wiener process employed by the Langevin dynamics. Exactly 1 or 6 positive integer values are expected. A single value is replicated to fill up the full seed array with 6 numbers. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L333)\]
