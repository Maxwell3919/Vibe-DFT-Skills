# CP2K official manual snapshot: xas

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html
- Raw SHA-256: c253095cab627a11b9ad3dbc8e5c74e0ce53ee0bfb4d8183bc2697b38f107843
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# XAS

**References:** [Iannuzzi2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2007)

Controls transition-potential and delta-SCF calculations of core-level excitation spectra. The occupied states from which the excitations are calculated should be specified. Localization of the orbitals may be useful. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L88)\]

Subsections

-   [LOCALIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS/LOCALIZE.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS/PRINT.html)
-   [SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS/SCF.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.XAS.SECTION_PARAMETERS")

-   [ADDED\_MOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.ADDED_MOS "CP2K_INPUT.FORCE_EVAL.DFT.XAS.ADDED_MOS")

-   [ATOMS\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.ATOMS_LIST "CP2K_INPUT.FORCE_EVAL.DFT.XAS.ATOMS_LIST")

-   [DIPOLE\_FORM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.DIPOLE_FORM "CP2K_INPUT.FORCE_EVAL.DFT.XAS.DIPOLE_FORM")

-   [EPS\_ADDED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.EPS_ADDED "CP2K_INPUT.FORCE_EVAL.DFT.XAS.EPS_ADDED")

-   [MAX\_ITER\_ADDED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.MAX_ITER_ADDED "CP2K_INPUT.FORCE_EVAL.DFT.XAS.MAX_ITER_ADDED")

-   [METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.XAS.METHOD")

-   [NGAUSS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.NGAUSS "CP2K_INPUT.FORCE_EVAL.DFT.XAS.NGAUSS")

-   [ORBITAL\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.ORBITAL_LIST "CP2K_INPUT.FORCE_EVAL.DFT.XAS.ORBITAL_LIST")

-   [OVERLAP\_THRESHOLD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.OVERLAP_THRESHOLD "CP2K_INPUT.FORCE_EVAL.DFT.XAS.OVERLAP_THRESHOLD")

-   [RESTART](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.RESTART "CP2K_INPUT.FORCE_EVAL.DFT.XAS.RESTART")

-   [SPIN\_CHANNEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.SPIN_CHANNEL "CP2K_INPUT.FORCE_EVAL.DFT.XAS.SPIN_CHANNEL")

-   [STATE\_SEARCH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.STATE_SEARCH "CP2K_INPUT.FORCE_EVAL.DFT.XAS.STATE_SEARCH")

-   [STATE\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.STATE_TYPE "CP2K_INPUT.FORCE_EVAL.DFT.XAS.STATE_TYPE")

-   [WFN\_RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.WFN_RESTART_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.XAS.WFN_RESTART_FILE_NAME")

-   [XAS\_CORE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.XAS_CORE "CP2K_INPUT.FORCE_EVAL.DFT.XAS.XAS_CORE")

-   [XAS\_TOT\_EL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.XAS_TOT_EL "CP2K_INPUT.FORCE_EVAL.DFT.XAS.XAS_TOT_EL")

-   [XES\_CORE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.XES_CORE "CP2K_INPUT.FORCE_EVAL.DFT.XAS.XES_CORE")

-   [XES\_EMPTY\_HOMO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html#CP2K_INPUT.FORCE_EVAL.DFT.XAS.XES_EMPTY_HOMO "CP2K_INPUT.FORCE_EVAL.DFT.XAS.XES_EMPTY_HOMO")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&XAS T*

controls the activation of core-level spectroscopy simulations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L97)\]

### ADDED\_MOS*: integer* *\= \-1*

**Usage:** *ADDED\_MOS {integer}*

Number of additional MOS added spin up only \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L231)\]

### ATOMS\_LIST*: integer\[ \]*

**Keyword can be repeated.**

**Aliases:** AT\_LIST

**Usage:** *ATOMS\_LIST {integer} {integer} .. {integer}*

Indexes of the atoms to be excited. This keyword can be repeated several times (useful if you have to specify many indexes). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L204)\]

### DIPOLE\_FORM*: enum* *\= VELOCITY*

**Aliases:** DIP\_FORM

**Usage:** *DIPOLE\_FORM string*

**Valid values:**

-   `LENGTH` Length form ⟨ i | e r | j ⟩

-   `VELOCITY` Velocity form ⟨ i | d/dr | j ⟩


Type of integral to get the oscillator strengths in the diipole approximation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L156)\]

### EPS\_ADDED*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_ADDED 1.e-6*

target accuracy incalculation of the added orbitals \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L243)\]

### MAX\_ITER\_ADDED*: integer* *\= 2999*

**Usage:** *MAX\_ITER\_ADDED 100*

maximum number of iteration in calculation of added orbitals \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L237)\]

### METHOD*: enum* *\= NONE*

**Aliases:** XAS\_METHOD

**Usage:** *METHOD TP\_HH*

**Valid values:**

-   `NONE` No core electron spectroscopy

-   `TP_HH` Transition potential half-hole

-   `TP_FH` Transition potential full-hole

-   `TP_VAL` Hole in homo for X-ray emission only

-   `TP_XHH` Transition potential excited half-hole

-   `TP_XFH` Transition potential excited full-hole

-   `DSCF` DSCF calculations to compute the first (core)excited state

-   `TP_FLEX` Transition potential with generalized core occupation and total number of electrons


Method to be used to calculate core-level excitation spectra \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L105)\]

### NGAUSS*: integer* *\= 3*

**Usage:** *NGAUSS {integer}*

Number of gto’s for the expansion of the STO of the type given by STATE\_TYPE \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L249)\]

### ORBITAL\_LIST*: integer\[ \]*

**Keyword can be repeated.**

**Aliases:** ORBITAL\_LIST

**Usage:** *ORBITAL\_LIST {integer} {integer} .. {integer}*

Indices of the localized orbitals to be excited. This keyword can be repeated several times (useful if you have to specify many indexes). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L221)\]

### OVERLAP\_THRESHOLD*: real* *\= 1.00000000E+000*

**Usage:** *OVERLAP\_THRESHOLD 8.e-1*

Threshold for including more than one initial core excited state per atom. The threshold is taken relative to the maximum overlap. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L214)\]

### RESTART*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *RESTART*

Restart the excited state if the restart file exists \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L256)\]

### SPIN\_CHANNEL*: integer* *\= 1*

**Usage:** *SPIN\_CHANNEL 1*

\# Spin channel of the excited orbital \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L197)\]

### STATE\_SEARCH*: integer* *\= \-1*

**Usage:** *STATE\_SEARCH 1*

\# of states where to look for the one to be excited \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L190)\]

### STATE\_TYPE*: enum* *\= 1S*

**Aliases:** TYPE

**Usage:** *STATE\_TYPE 1S*

**Valid values:**

-   `1S` 1s orbitals

-   `2S` 2s orbitals

-   `2P` 2p orbitals

-   `3S` 3s orbitals

-   `3P` 3p orbitals

-   `3D` 3d orbitals

-   `4S` 4s orbitals

-   `4P` 4p orbitals

-   `4D` 4d orbitals

-   `4F` 4f orbitals


Type of the orbitals that are excited for the xas spectra calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L177)\]

### WFN\_RESTART\_FILE\_NAME*: string*

**Aliases:** RESTART\_FILE\_NAME

**Usage:** *WFN\_RESTART\_FILE\_NAME*

Root of the file names where to read the MOS from which to restart the calculation of the core level excited states \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L263)\]

### XAS\_CORE*: real* *\= 5.00000000E-001*

**Usage:** *XAS\_CORE 0.5*

Occupation of the core state in XAS calculation by TP\_FLEX. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L123)\]

### XAS\_TOT\_EL*: real* *\= \-1.00000000E+000*

**Usage:** *XAS\_TOT\_EL 10*

Total number of electrons for spin channel alpha, in XAS calculation by TP\_FLEX. If it is a negative value, the number of electrons is set to GS number of electrons minus the amount subtracted from the core state \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L130)\]

### XES\_CORE*: real* *\= 1.00000000E+000*

**Usage:** *XES\_CORE 0.5*

Occupation of the core state in XES calculation by TP\_VAL. The HOMO is emptied by the same amount. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L139)\]

### XES\_EMPTY\_HOMO*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *XES\_EMPTY\_HOMO*

Set the occupation of the HOMO in XES calculation by TP\_VAL. The HOMO can be emptied or not, if the core is still full. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_xas.F#L147)\]
