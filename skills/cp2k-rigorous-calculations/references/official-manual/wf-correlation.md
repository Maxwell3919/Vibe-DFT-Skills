# CP2K official manual snapshot: wf-correlation

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html
- Raw SHA-256: 864fa16348adb1b1736c97314dda8da37071bfd68e5c356c31b4b0395b567f46
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# WF\_CORRELATION

**Section can be repeated.**

**References:** [DelBen2012](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#delben2012), [DelBen2013](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#delben2013), [DelBen2015](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#delben2015), [DelBen2015b](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#delben2015b), [Rybkin2016](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#rybkin2016), [Wilhelm2016](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#wilhelm2016), [Wilhelm2016b](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#wilhelm2016b), [Wilhelm2017](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#wilhelm2017), [Wilhelm2018](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#wilhelm2018), [Stein2022](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stein2022), [Stein2024](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stein2024), [Bussy2023](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#bussy2023)

Controls wavefunction-based correlation methods such as MP2, RI-MP2, RI-SOS-MP2, RI-RPA, and GW inside RI-RPA. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L84)\]

Subsections

-   [CANONICAL\_GRADIENTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/CANONICAL_GRADIENTS.html)
-   [INTEGRALS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/INTEGRALS.html)
-   [LOW\_SCALING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/LOW_SCALING.html)
-   [MP2](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/MP2.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/PRINT.html)
-   [RI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/RI.html)
-   [RI\_MP2](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/RI_MP2.html)
-   [RI\_RPA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/RI_RPA.html)
-   [RI\_SOS\_MP2](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION/RI_SOS_MP2.html)

## Keywords

-   [E\_GAP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.E_GAP "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.E_GAP")

-   [E\_RANGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.E_RANGE "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.E_RANGE")

-   **[GROUP\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.GROUP_SIZE "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.GROUP_SIZE")**

-   [MEMORY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.MEMORY "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.MEMORY")

-   **[SCALE\_S](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.SCALE_S "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.SCALE_S")**

-   **[SCALE\_T](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html#CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.SCALE_T "CP2K_INPUT.FORCE_EVAL.DFT.XC.WF_CORRELATION.SCALE_T")**


## Keyword descriptions

### E\_GAP*: real* *\= \-1.00000000E+000*

**Usage:** *E\_GAP 0.5*

Gap energy for integration grids in Hartree. Defaults to -1.0 (automatic determination). Recommended to set if several RPA or SOS-MP2 gradient calculations are requested or to be restarted. In this way, differences of integration grids across different runs are removed as CP2K does not include derivatives thereof. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L104)\]

### E\_RANGE*: real* *\= \-1.00000000E+000*

**Usage:** *E\_RANGE 10.0*

Energy range (ratio of largest and smallest) energy difference of unoccupied and occupied orbitals for integration grids. Defaults to 0.0 (automatic determination). Recommended to set if several RPA or SOS-MP2 gradient calculations are requested or to be restarted. In this way, differences of integration grids across different runs are removed as CP2K does not include derivatives thereof. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L116)\]

### GROUP\_SIZE*: integer* *\= 1*

**Aliases:** NUMBER\_PROC

**Usage:** *GROUP\_SIZE 2*

**Mentions:** ⭐[Random-Phase Approximation and Laplace-Transformed Scaled-Opposite-Spin-MP2](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/rpa.html)

Group size used in the computation of GPW and MME integrals and the MP2 correlation energy. The group size must be a divisor of the total number of MPI ranks. A smaller group size (for example the number of MPI ranks per node) accelerates the computation of integrals but a too large group size increases communication costs. A too small group size may lead to out of memory. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L149)\]

### MEMORY*: real* *\= 1.02400000E+003*

**Usage:** *MEMORY 1500*

Maximum allowed total memory usage during MP2 and related WF\_CORRELATION methods \[MiB\]. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L95)\]

### SCALE\_S*: real* *\= 1.00000000E+000*

**Usage:** *SCALE\_S 1.0*

**Mentions:** ⭐[Møller–Plesset Perturbation Theory](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/mp2.html), ⭐[Random-Phase Approximation and Laplace-Transformed Scaled-Opposite-Spin-MP2](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/rpa.html)

Scaling factor of the singlet energy component (opposite spin, OS) of the MP2, RI-MP2 and SOS-MP2 correlation energy. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L129)\]

### SCALE\_T*: real* *\= 1.00000000E+000*

**Usage:** *SCALE\_T 1.0*

**Mentions:** ⭐[Møller–Plesset Perturbation Theory](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/mp2.html)

Scaling factor of the triplet energy component (same spin, SS) of the MP2 and RI-MP2 correlation energy. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_mp2.F#L139)\]
