# CP2K official manual snapshot: vdw-potential

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL.html
- Raw SHA-256: 589c30fe8a9e7ecbc858d26ca95f5979063adca22f4813a9fc88b6748f3fe64d
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# VDW\_POTENTIAL

**References:** [Grimme2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#grimme2006), [Tran2013](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#tran2013)

This section combines all possible additional dispersion corrections to the normal XC functionals. This can be more functionals or simple empirical pair potentials. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L932)\]

Subsections

-   [NON\_LOCAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL/NON_LOCAL.html)
-   [PAIR\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL/PAIR_POTENTIAL.html)

## Keywords

-   [POTENTIAL\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.VDW_POTENTIAL.POTENTIAL_TYPE "CP2K_INPUT.FORCE_EVAL.DFT.XC.VDW_POTENTIAL.POTENTIAL_TYPE")


## Keyword descriptions

### POTENTIAL\_TYPE*: enum* *\= NONE*

**Aliases:** DISPERSION\_FUNCTIONAL

**Usage:** *POTENTIAL\_TYPE (NONE|PAIR\_POTENTIAL|NON\_LOCAL)*

**Valid values:**

-   `NONE` No dispersion/van der Waals functional.

-   `PAIR_POTENTIAL` Pair potential van der Waals density functional, including Grimme’s empirical DFT-D methods.

-   `NON_LOCAL` Nonlocal van der Waals density functional; more rigorous in principle, but significantly more time-consuming.


Type of dispersion/vdW functional or potential to use \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xc.F#L940)\]
