# CP2K official manual snapshot: hfx

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html
- Raw SHA-256: 1c5bbbff7aa7d8305e2c92f7a8be3b02825e754c9c0a22cb371de9b2ac3d878e
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# HF

**Section can be repeated.**

**References:** [Guidon2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2008), [Guidon2009](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#guidon2009)

Controls Hartree-Fock exchange for hybrid DFT, Hartree-Fock, and related post-Hartree-Fock workflows. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L65)\]

Subsections

-   [ACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/ACE.html)
-   [HF\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/HF_INFO.html)
-   [INTERACTION\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/INTERACTION_POTENTIAL.html)
-   [LOAD\_BALANCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/LOAD_BALANCE.html)
-   [MEMORY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/MEMORY.html)
-   [PERIODIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/PERIODIC.html)
-   [RI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/RI.html)
-   [SCREENING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html)

## Keywords

-   [FRACTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.FRACTION "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.FRACTION")

-   [HFX\_LIBRARY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.HFX_LIBRARY "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.HFX_LIBRARY")

-   [PW\_HFX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.PW_HFX "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.PW_HFX")

-   [PW\_HFX\_BLOCKSIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.PW_HFX_BLOCKSIZE "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.PW_HFX_BLOCKSIZE")

-   [TREAT\_LSD\_IN\_CORE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.TREAT_LSD_IN_CORE "CP2K_INPUT.FORCE_EVAL.DFT.XC.HF.TREAT_LSD_IN_CORE")


## Keyword descriptions

### FRACTION*: real* *\= 1.00000000E+000*

**Usage:** *FRACTION 1.0*

Fraction of Hartree-Fock exchange to add to the total energy. 1.0 implies standard Hartree-Fock if used with XC\_FUNCTIONAL NONE. NOTE: In a mixed potential calculation this should be set to 1.0, otherwise all parts are multiplied with this factor. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L73)\]

### HFX\_LIBRARY*: enum* *\= LIBINT*

**Usage:** *HFX\_LIBRARY libGint*

**Valid values:**

-   `LIBINT` libint: use the libint library to compute the 2 electron integrals for HFX/r

-   `LIBGINT` libGint: use the libGint library to accelerate the calculation of the HF exchange on (cuda) GPUs /r

-   `BOTH` both: temporary debug option, will run both libint and libGint and check if the fock matrix is within tolerance


Which library should be used in the calculation of the HF exchange (Libint (cpu, default), libGint(gpu, cuda), both(debug,temporary) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L91)\]

### PW\_HFX*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *PW\_HFX FALSE*

Compute the Hartree-Fock energy also in the plane wave basis. The value is ignored, and intended for debugging only. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L107)\]

### PW\_HFX\_BLOCKSIZE*: integer* *\= 20*

**Usage:** *PW\_HFX\_BLOCKSIZE 20*

Improve the performance of pw\_hfx at the cost of some additional memory by storing the realspace representation of PW\_HFX\_BLOCKSIZE states. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L114)\]

### TREAT\_LSD\_IN\_CORE*: logical* *\= F*

**Usage:** *TREAT\_LSD\_IN\_CORE TRUE*

Determines how spin densities are taken into account. If true, the beta spin density is included via a second in core call. If false, alpha and beta spins are done in one shot \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_hfx.F#L82)\]
