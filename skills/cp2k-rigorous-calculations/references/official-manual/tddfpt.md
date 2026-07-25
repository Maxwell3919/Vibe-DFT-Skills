# CP2K official manual snapshot: tddfpt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html
- Raw SHA-256: 318c22758b42349f3cd6737d5a6c5ec9432335542bec2959e5bcd6d326efa174
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# TDDFPT

**References:** [Iannuzzi2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2005), [Hanasaki2025](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#hanasaki2025), [HernandezSegura2025](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#hernandezsegura2025)

Controls time-dependent density functional perturbation theory (TDDFPT) calculations for electronic excitations and related properties. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1627)\]

Subsections

-   [DIPOLE\_MOMENTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/DIPOLE_MOMENTS.html)
-   [LINRES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/LINRES.html)
-   [LRIGPW](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/LRIGPW.html)
-   [MGRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/MGRID.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/PRINT.html)
-   [REDUCED\_EXCITATION\_SPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/REDUCED_EXCITATION_SPACE.html)
-   [SOC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/SOC.html)
-   [STDA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/STDA.html)
-   [XC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT/XC.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.SECTION_PARAMETERS")

-   [ADMM\_KERNEL\_CORRECTION\_SYMMETRIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ADMM_KERNEL_CORRECTION_SYMMETRIC "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ADMM_KERNEL_CORRECTION_SYMMETRIC")

-   [ADMM\_KERNEL\_XC\_CORRECTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ADMM_KERNEL_XC_CORRECTION "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ADMM_KERNEL_XC_CORRECTION")

-   [AUTO\_BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.AUTO_BASIS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.AUTO_BASIS")

-   **[CONVERGENCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.CONVERGENCE "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.CONVERGENCE")**

-   [DIRECTIONAL\_EXCITON\_DESCRIPTORS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DIRECTIONAL_EXCITON_DESCRIPTORS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DIRECTIONAL_EXCITON_DESCRIPTORS")

-   [DO\_BSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE")

-   [DO\_BSE\_GW\_ONLY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE_GW_ONLY "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE_GW_ONLY")

-   [DO\_BSE\_W\_ONLY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE_W_ONLY "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_BSE_W_ONLY")

-   [DO\_LRIGPW](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_LRIGPW "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_LRIGPW")

-   [DO\_SMEARING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_SMEARING "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.DO_SMEARING")

-   [EOS\_SHIFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EOS_SHIFT "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EOS_SHIFT")

-   **[EV\_SHIFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EV_SHIFT "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EV_SHIFT")**

-   [EXCITON\_DESCRIPTORS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EXCITON_DESCRIPTORS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.EXCITON_DESCRIPTORS")

-   **[KERNEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.KERNEL "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.KERNEL")**

-   [MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MAX_ITER "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MAX_ITER")

-   [MAX\_KV](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MAX_KV "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MAX_KV")

-   **[MIN\_AMPLITUDE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MIN_AMPLITUDE "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.MIN_AMPLITUDE")**

-   **[NLUMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NLUMO "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NLUMO")**

-   [NPROC\_STATE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NPROC_STATE "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NPROC_STATE")

-   **[NSTATES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NSTATES "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.NSTATES")**

-   [OE\_CORR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.OE_CORR "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.OE_CORR")

-   [ORTHOGONAL\_EPS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ORTHOGONAL_EPS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.ORTHOGONAL_EPS")

-   **[RESTART](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.RESTART "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.RESTART")**

-   **[RKS\_TRIPLETS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.RKS_TRIPLETS "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.RKS_TRIPLETS")**

-   [SPINFLIP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.SPINFLIP "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.SPINFLIP")

-   **[WFN\_RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html#CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.WFN_RESTART_FILE_NAME "CP2K_INPUT.FORCE_EVAL.PROPERTIES.TDDFPT.WFN_RESTART_FILE_NAME")**


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

Activates the TDDFPT procedure. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1635)\]

### ADMM\_KERNEL\_CORRECTION\_SYMMETRIC*: logical* *\= T*

**Lone keyword:** `T`

ADMM correction functional in kernel is applied symmetrically. Original implementation is using a non-symmetric formula. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1790)\]

### ADMM\_KERNEL\_XC\_CORRECTION*: logical* *\= T*

**Lone keyword:** `T`

Use/Ignore ADMM correction xc functional for TD kernel. XC correction functional is defined in ground state XC section. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1782)\]

### AUTO\_BASIS*: string\[ \]* *\= X X*

**Keyword can be repeated.**

**Usage:** *AUTO\_BASIS {basis\_type} {basis\_size}*

Specify size of automatically generated auxiliary basis sets: Options={small,medium,large,huge} \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1805)\]

### CONVERGENCE*: real* *\= 1.00000000E-005 \[hartree\]*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Target accuracy for excited state energies. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1743)\]

### DIRECTIONAL\_EXCITON\_DESCRIPTORS*: logical* *\= F*

Print cartesian components of exciton descriptors. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1828)\]

### DO\_BSE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DO\_BSE*

Choosing BSE kernel. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1941)\]

### DO\_BSE\_GW\_ONLY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DO\_BSE\_GW\_ONLY*

Debug option for BSE kernel. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1953)\]

### DO\_BSE\_W\_ONLY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DO\_BSE\_W\_ONLY*

Debug option for BSE kernel. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1947)\]

### DO\_LRIGPW*: logical* *\= F*

Local resolution of identity for Coulomb contribution. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1798)\]

### DO\_SMEARING*: logical* *\= F*

**Lone keyword:** `T`

Implying smeared occupation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1813)\]

### EOS\_SHIFT*: real* *\= 0.00000000E+000 \[eV\]*

**Aliases:** OPEN\_SHELL\_SHIFT

**Usage:** *EOS\_SHIFT 0.200*

Constant shift of open shell eigenvalues. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1732)\]

### EV\_SHIFT*: real* *\= 0.00000000E+000 \[eV\]*

**Aliases:** VIRTUAL\_SHIFT

**Usage:** *EV\_SHIFT 0.500*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Constant shift of virtual state eigenvalues. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1722)\]

### EXCITON\_DESCRIPTORS*: logical* *\= F*

Compute exciton descriptors. Details given in Manual section about Bethe Salpeter equation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1820)\]

### KERNEL*: enum* *\= FULL*

**Usage:** *KERNEL FULL*

**Valid values:**

-   `FULL`

-   `STDA`

-   `NONE`


**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Options to compute the kernel \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1683)\]

### MAX\_ITER*: integer* *\= 50*

Maximal number of iterations to be performed. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1651)\]

### MAX\_KV*: integer* *\= 5000*

Maximal number of Krylov space vectors. Davidson iterations will be restarted upon reaching this limit. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1658)\]

### MIN\_AMPLITUDE*: real* *\= 5.00000000E-002*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

The smallest excitation amplitude to print. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1750)\]

### NLUMO*: integer* *\= \-1*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Number of unoccupied orbitals to consider. Default is to use all unoccupied orbitals (-1). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1666)\]

### NPROC\_STATE*: integer* *\= 0*

Number of MPI processes to be used per excited state. Default is to use all MPI processes (0). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1674)\]

### NSTATES*: integer* *\= 1*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Number of excited states to converge. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1644)\]

### OE\_CORR*: enum* *\= NONE*

**Valid values:**

-   `NONE` No orbital correction scheme is used

-   `LB94` van Leeuwen and Baerends. PRA, 49:2421, 1994

-   `GLLB` Gritsenko, van Leeuwen, van Lenthe, Baerends. PRA, 51:1944, 1995

-   `SAOP` Gritsenko, Schipper, Baerends. Chem. Phys. Lett., 302:199, 1999

-   `SHIFT` Constant shift of virtual and/or open-shell orbitals


Orbital energy correction potential. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1708)\]

### ORTHOGONAL\_EPS*: real* *\= 1.00000000E-004*

The largest possible overlap between the ground state and orthogonalised excited state wave-functions. Davidson iterations will be restarted when the overlap goes beyond this threshold in order to prevent numerical instability. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1757)\]

### RESTART*: logical* *\= F*

**Lone keyword:** `T`

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Restart the TDDFPT calculation if a restart file exists \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1768)\]

### RKS\_TRIPLETS*: logical* *\= F*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Compute triplet excited states using spin-unpolarised molecular orbitals. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1775)\]

### SPINFLIP*: enum* *\= NONE*

**Usage:** *SPINFLIP NONCOLLINEAR*

**Valid values:**

-   `NONE` Only molecular orbital energy differences are considered

-   `COLLINEAR` MO energy diferences and Fock exchange contributions are considered

-   `NONCOLLINEAR` MO energy differences, Fock exchange and Noncollinear local exchange-correlation kernel are considered


**References:** [HernandezSegura2025](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#hernandezsegura2025)

Selects the type of spin-flip TDDFPT kernel \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1693)\]

### WFN\_RESTART\_FILE\_NAME*: string*

**Aliases:** RESTART\_FILE\_NAME

**Usage:** *WFN\_RESTART\_FILE\_NAME*

**Mentions:** ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html)

Name of the wave function restart file, may include a path. If no file is specified, the default is to open the file as generated by the wave function restart print key. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_properties_dft.F#L1836)\]
