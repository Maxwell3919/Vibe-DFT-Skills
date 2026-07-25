# CP2K official manual snapshot: qs

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html
- Raw SHA-256: 94d335636fd90dd85be5360505eb6cd126f4435236d05a62381a53682b1da346
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# QS

parameters needed to set up the Quickstep framework \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L84)\]

Subsections

-   [CDFT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/CDFT.html)
-   [DDAPC\_RESTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/DDAPC_RESTRAINT.html)
-   [DFTB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/DFTB.html)
-   [DISTRIBUTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/DISTRIBUTION.html)
-   [LRIGPW](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/LRIGPW.html)
-   [MULLIKEN\_RESTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/MULLIKEN_RESTRAINT.html)
-   [OPTIMIZE\_LRI\_BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/OPTIMIZE_LRI_BASIS.html)
-   [OPT\_DMFET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/OPT_DMFET.html)
-   [OPT\_EMBED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/OPT_EMBED.html)
-   [S2\_RESTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/S2_RESTRAINT.html)
-   [SE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/SE.html)
-   [XTB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS/XTB.html)

## Keywords

-   [ALMO\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.ALMO_SCF "CP2K_INPUT.FORCE_EVAL.DFT.QS.ALMO_SCF")

-   [ALPHA0\_HARD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.ALPHA0_HARD "CP2K_INPUT.FORCE_EVAL.DFT.QS.ALPHA0_HARD")

-   [ALPHA\_WEIGHTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.ALPHA_WEIGHTS "CP2K_INPUT.FORCE_EVAL.DFT.QS.ALPHA_WEIGHTS")

-   [CLUSTER\_EMBED\_SUBSYS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.CLUSTER_EMBED_SUBSYS "CP2K_INPUT.FORCE_EVAL.DFT.QS.CLUSTER_EMBED_SUBSYS")

-   [CORE\_PPL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.CORE_PPL "CP2K_INPUT.FORCE_EVAL.DFT.QS.CORE_PPL")

-   [DFET\_EMBEDDED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.DFET_EMBEDDED "CP2K_INPUT.FORCE_EVAL.DFT.QS.DFET_EMBEDDED")

-   [DMFET\_EMBEDDED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.DMFET_EMBEDDED "CP2K_INPUT.FORCE_EVAL.DFT.QS.DMFET_EMBEDDED")

-   [EMBED\_CUBE\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_CUBE_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_CUBE_FILE_NAME")

-   [EMBED\_RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_RESTART_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_RESTART_FILE_NAME")

-   [EMBED\_SPIN\_CUBE\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_SPIN_CUBE_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.QS.EMBED_SPIN_CUBE_FILE_NAME")

-   **[EPSFIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSFIT "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSFIT")**

-   [EPSISO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSISO "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSISO")

-   **[EPSRHO0](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSRHO0 "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSRHO0")**

-   **[EPSSVD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSSVD "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPSSVD")**

-   [EPS\_CORE\_CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_CORE_CHARGE "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_CORE_CHARGE")

-   [EPS\_CPC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_CPC "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_CPC")

-   **[EPS\_DEFAULT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_DEFAULT "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_DEFAULT")**

-   [EPS\_FILTER\_MATRIX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_FILTER_MATRIX "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_FILTER_MATRIX")

-   [EPS\_GVG\_RSPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_GVG_RSPACE "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_GVG_RSPACE")

-   [EPS\_KG\_ORB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_KG_ORB "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_KG_ORB")

-   [EPS\_PGF\_ORB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PGF_ORB "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PGF_ORB")

-   [EPS\_PPL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PPL "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PPL")

-   [EPS\_PPNL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PPNL "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_PPNL")

-   [EPS\_RHO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO")

-   [EPS\_RHO\_GSPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO_GSPACE "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO_GSPACE")

-   [EPS\_RHO\_RSPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO_RSPACE "CP2K_INPUT.FORCE_EVAL.DFT.QS.EPS_RHO_RSPACE")

-   **[EXTRAPOLATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EXTRAPOLATION "CP2K_INPUT.FORCE_EVAL.DFT.QS.EXTRAPOLATION")**

-   **[EXTRAPOLATION\_ORDER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.EXTRAPOLATION_ORDER "CP2K_INPUT.FORCE_EVAL.DFT.QS.EXTRAPOLATION_ORDER")**

-   [FORCE\_PAW](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.FORCE_PAW "CP2K_INPUT.FORCE_EVAL.DFT.QS.FORCE_PAW")

-   [GAPW\_1C\_BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.GAPW_1C_BASIS "CP2K_INPUT.FORCE_EVAL.DFT.QS.GAPW_1C_BASIS")

-   [GAPW\_ACCURATE\_XCINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.GAPW_ACCURATE_XCINT "CP2K_INPUT.FORCE_EVAL.DFT.QS.GAPW_ACCURATE_XCINT")

-   [HIGH\_LEVEL\_EMBED\_SUBSYS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.HIGH_LEVEL_EMBED_SUBSYS "CP2K_INPUT.FORCE_EVAL.DFT.QS.HIGH_LEVEL_EMBED_SUBSYS")

-   [KG\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.KG_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.QS.KG_METHOD")

-   [LADDN0](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.LADDN0 "CP2K_INPUT.FORCE_EVAL.DFT.QS.LADDN0")

-   [LMAXN0](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.LMAXN0 "CP2K_INPUT.FORCE_EVAL.DFT.QS.LMAXN0")

-   [LMAXN1](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.LMAXN1 "CP2K_INPUT.FORCE_EVAL.DFT.QS.LMAXN1")

-   [LS\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.LS_SCF "CP2K_INPUT.FORCE_EVAL.DFT.QS.LS_SCF")

-   [MAX\_RAD\_LOCAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.MAX_RAD_LOCAL "CP2K_INPUT.FORCE_EVAL.DFT.QS.MAX_RAD_LOCAL")

-   **[METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.QS.METHOD")**

-   [MIN\_PAIR\_LIST\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.MIN_PAIR_LIST_RADIUS "CP2K_INPUT.FORCE_EVAL.DFT.QS.MIN_PAIR_LIST_RADIUS")

-   [PW\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID "CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID")

-   [PW\_GRID\_BLOCKED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID_BLOCKED "CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID_BLOCKED")

-   [PW\_GRID\_LAYOUT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID_LAYOUT "CP2K_INPUT.FORCE_EVAL.DFT.QS.PW_GRID_LAYOUT")

-   [QUADRATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.QUADRATURE "CP2K_INPUT.FORCE_EVAL.DFT.QS.QUADRATURE")

-   [REF\_EMBED\_SUBSYS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.REF_EMBED_SUBSYS "CP2K_INPUT.FORCE_EVAL.DFT.QS.REF_EMBED_SUBSYS")

-   [STO\_NG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.STO_NG "CP2K_INPUT.FORCE_EVAL.DFT.QS.STO_NG")

-   [TRANSPORT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html#CP2K_INPUT.FORCE_EVAL.DFT.QS.TRANSPORT "CP2K_INPUT.FORCE_EVAL.DFT.QS.TRANSPORT")


## Keyword descriptions

### ALMO\_SCF*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ALMO\_SCF*

Perform ALMO SCF \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L283)\]

### ALPHA0\_HARD*: real* *\= 0.00000000E+000*

**Aliases:** ALPHA0\_H ,ALPHA0

**Usage:** *ALPHA0\_HARD real*

GAPW: Exponent for hard compensation charge \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L202)\]

### ALPHA\_WEIGHTS*: real* *\= 6.00000000E+000*

**Usage:** *ALPHA\_WEIGHTS 10.0*

Gaussian exponent reference (rc=1.2 Bohr) for accurate integration in GAPW. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L261)\]

### CLUSTER\_EMBED\_SUBSYS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *CLUSTER\_EMBED\_SUBSYS FALSE*

A cluster treated with DFT in DFT embedding. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L311)\]

### CORE\_PPL*: enum* *\= ANALYTIC*

**Usage:** *CORE\_PPL ANALYTIC*

**Valid values:**

-   `ANALYTIC` Analytic integration of integrals

-   `GRID` Numerical integration on real space grid. Lumped together with core charge


Specifies the method used to calculate the local pseudopotential contribution. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L494)\]

### DFET\_EMBEDDED*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DFET\_EMBEDDED FALSE*

Calculation with DFT-embedding potential. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L325)\]

### DMFET\_EMBEDDED*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DMFET\_EMBEDDED FALSE*

Calculation with DM embedding potential. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L332)\]

### EMBED\_CUBE\_FILE\_NAME*: string*

**Usage:** *EMBED\_CUBE\_FILE\_NAME*

Root of the file name where to read the embedding potential (guess) as a cube. Whitespace-separated cube values are accepted. If adjacent values are written without whitespace, each value must occupy a 13-character E13.5 field, as in CP2K-generated cube files. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L513)\]

### EMBED\_RESTART\_FILE\_NAME*: string*

**Usage:** *EMBED\_RESTART\_FILE\_NAME*

Root of the file name where to read the embedding potential guess. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L505)\]

### EMBED\_SPIN\_CUBE\_FILE\_NAME*: string*

**Usage:** *EMBED\_SPIN\_CUBE\_FILE\_NAME*

Root of the file name where to read the spin part of the embedding potential (guess) as a cube. Whitespace-separated cube values are accepted. If adjacent values are written without whitespace, each value must occupy a 13-character E13.5 field, as in CP2K-generated cube files. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L523)\]

### EPSFIT*: real* *\= 1.00000000E-004*

**Aliases:** EPS\_FIT

**Usage:** *EPSFIT real*

**Mentions:** ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)

GAPW: tolerance controlling the split of Gaussian basis functions into hard atom-centered and soft grid-expanded parts. Smaller values include harder Gaussians in the soft density and can require a larger MGRID cutoff. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L170)\]

### EPSISO*: real* *\= 1.00000000E-012*

**Aliases:** EPS\_ISO

**Usage:** *EPSISO real*

GAPW: precision to determine an isolated projector \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L179)\]

### EPSRHO0*: real* *\= 1.00000000E-006*

**Aliases:** EPSVRHO0 ,EPS\_VRHO0

**Usage:** *EPSRHO0 real*

**Mentions:** ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)

GAPW: tolerance used to determine the range of the V(rho0-rho0\_soft) compensation contribution. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L194)\]

### EPSSVD*: real* *\= 1.00000000E-008*

**Aliases:** EPS\_SVD

**Usage:** *EPS\_SVD real*

**Mentions:** ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)

GAPW: tolerance used in the singular value decomposition of the projector matrix. Smaller values can improve numerical accuracy at increased cost. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L186)\]

### EPS\_CORE\_CHARGE*: real*

**Usage:** *EPS\_CORE\_CHARGE real*

Precision for mapping the core charges.Overrides EPS\_DEFAULT/100.0 value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L97)\]

### EPS\_CPC*: real*

**Usage:** *EPS\_CPC real*

Sets precision of the GAPW projection. Overrides EPS\_DEFAULT value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L138)\]

### EPS\_DEFAULT*: real* *\= 1.00000000E-010*

**Usage:** *EPS\_DEFAULT real*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Try setting all EPS\_xxx to values leading to an energy correct up to EPS\_DEFAULT \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L91)\]

### EPS\_FILTER\_MATRIX*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_FILTER\_MATRIX 1.0E-6*

Sets the threshold for filtering matrix elements. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L164)\]

### EPS\_GVG\_RSPACE*: real*

**Aliases:** EPS\_GVG

**Usage:** *EPS\_GVG\_RSPACE real*

Sets precision of the realspace KS matrix element integration. Overrides SQRT(EPS\_DEFAULT) value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L104)\]

### EPS\_KG\_ORB*: real*

**Usage:** *EPS\_KG\_ORB 1.0E-8*

Sets precision used in coloring the subsets for the Kim-Gordon method. Overrides SQRT(EPS\_DEFAULT) value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L118)\]

### EPS\_PGF\_ORB*: real*

**Usage:** *EPS\_PGF\_ORB real*

Sets precision of the overlap matrix elements. Overrides SQRT(EPS\_DEFAULT) value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L111)\]

### EPS\_PPL*: real* *\= 1.00000000E-002*

**Usage:** *EPS\_PPL real*

Adjusts the precision for the local part of the pseudo potential. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L125)\]

### EPS\_PPNL*: real*

**Usage:** *EPS\_PPNL real*

Sets precision of the non-local part of the pseudo potential. Overrides sqrt(EPS\_DEFAULT) value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L132)\]

### EPS\_RHO*: real*

**Usage:** *EPS\_RHO real*

Sets precision of the density mapping on the grids.Overrides EPS\_DEFAULT value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L144)\]

### EPS\_RHO\_GSPACE*: real*

**Usage:** *EPS\_RHO\_GSPACE real*

Sets precision of the density mapping in gspace.Overrides EPS\_DEFAULT value. Overrides EPS\_RHO value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L157)\]

### EPS\_RHO\_RSPACE*: real*

**Usage:** *EPS\_RHO\_RSPACE real*

Sets precision of the density mapping in rspace.Overrides EPS\_DEFAULT value. Overrides EPS\_RHO value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L150)\]

### EXTRAPOLATION*: enum* *\= ASPC*

**Aliases:** INTERPOLATION ,WF\_INTERPOLATION

**Usage:** *EXTRAPOLATION PS*

**Valid values:**

-   `USE_GUESS` Use the method specified with SCF\_GUESS, i.e. no extrapolation

-   `USE_PREV_P` Use the previous density matrix

-   `USE_PREV_RHO_R` Legacy alias for USE\_PREV\_P, using the previous density matrix; deprecated

-   `LINEAR_WF` Linear extrapolation of the wavefunction (not available for k-points)

-   `LINEAR_P` Linear extrapolation of the density matrix

-   `LINEAR_PS` Linear extrapolation of the density matrix times the overlap matrix (not available for k-points)

-   `USE_PREV_WF` Use the previous wavefunction

-   `PS` Higher order extrapolation of the density matrix times the overlap matrix

-   `FROZEN` Frozen … (not available for k-points)

-   `ASPC` Always stable predictor corrector, similar to PS, but going for MD stability instead of initial guess accuracy.

-   `GEXT_PROJ` GExt extrapolation for the density matrix times the overlap matrix.

-   `GEXT_PROJ_QTR` Quasi time reversible GExt extrapolation for the density matrix times the overlap matrix.


**References:** [Kolafa2004](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#kolafa2004), [VandeVondele2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2005), [Kühne2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#kuhne2007)

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Extrapolation strategy for the wavefunction during e.g. MD. Not all options are available for all simulation methods. PS and ASPC are recommended, see also EXTRAPOLATION\_ORDER. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L415)\]

### EXTRAPOLATION\_ORDER*: integer* *\= 3*

**Usage:** *EXTRAPOLATION\_ORDER {integer}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Order for the PS, ASPC extrapolation (typically 2-4) or order for the GEXT\_PROJ, GEXT\_PROJ\_QTR extrapolation (typically 4-10). Higher order might bring more accuracy, but comes, for large systems, also at some cost. In some cases, a high order extrapolation is not stable, and the order needs to be reduced. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L455)\]

### FORCE\_PAW*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *FORCE\_PAW*

Use the GAPW scheme also for atoms with soft basis sets, i.e. the local densities are computed even if hard and soft should be equal. If this keyword is not set to true, those atoms with soft basis sets are treated by a GPW scheme, i.e. the corresponding density contribution goes on the global grid and is expanded in PW. This option nullifies the effect of the GPW\_TYPE in the atomic KIND \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L210)\]

### GAPW\_1C\_BASIS*: enum* *\= ORB*

**Usage:** *GAPW\_1C\_BASIS MEDIUM*

**Valid values:**

-   `ORB` Use orbital basis set.

-   `EXT_SMALL` Extension using Small number of primitive Gaussians.

-   `EXT_MEDIUM` Extension using Medium number of primitive Gaussians.

-   `EXT_LARGE` Extension using Large number of primitive Gaussians.

-   `EXT_VERY_LARGE` Extension using Very Large number of primitive Gaussians.


Specifies how to construct the GAPW one center basis set. Default is to use the primitives from the orbital basis. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L228)\]

### GAPW\_ACCURATE\_XCINT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *GAPW\_ACCURATE\_XCINT*

Use the accurate GAPW/GAPW\_XC XC integration scheme for one-center hard/soft density differences. This opt-in path covers regular GAPW/GAPW\_XC XC energy, potential, forces, mGGA/tau terms, NLCC, Fine-XC grids, local XC energy-density transfer, analytical stress, TDDFPT/response forces, ADMM-GAPW force paths, an ADMM-GAPW diagonal stress debug path, nonlocal vdW smoke coverage, representative k-point, XAS\_TDP, and RTBSE smoke cases, and KG GAPW/GAPW\_XC EMBED, EMBED\_RI, ATOMIC, and NONE cases. Regular-grid local energy and stress cube print keys keep their existing soft-grid semantics and are not changed by this keyword. The default remains off while this coverage is being prepared for a future default change. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L245)\]

### HIGH\_LEVEL\_EMBED\_SUBSYS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *HIGH\_LEVEL\_EMBED\_SUBSYS FALSE*

A cluster treated with a high-level method in DFT embedding. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L318)\]

### KG\_METHOD*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *KG\_METHOD*

**References:** [Iannuzzi2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2006), [Brelaz1979](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#brelaz1979), [Andermatt2016](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#andermatt2016)

Use a Kim-Gordon-like scheme. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L297)\]

### LADDN0*: integer* *\= 99*

**Usage:** *LADDN0 integer*

GAPW : integer added to the max L of the basis set, used to determine the maximum value of L for the compensation charge density. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L362)\]

### LMAXN0*: integer* *\= 2*

**Aliases:** LMAXRHO0

**Usage:** *LMAXN0 integer*

GAPW : max L number for the expansion compensation densities in spherical gaussians \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L354)\]

### LMAXN1*: integer* *\= \-1*

**Aliases:** LMAXRHO1

**Usage:** *LMAXN1 integer*

GAPW : max L number for expansion of the atomic densities in spherical gaussians \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L346)\]

### LS\_SCF*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LS\_SCF*

Perform a linear scaling SCF \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L276)\]

### MAX\_RAD\_LOCAL*: real* *\= 2.50000000E+001*

**Usage:** *MAX\_RAD\_LOCAL real*

GAPW : maximum radius of gaussian functions included in the generation of projectors \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L221)\]

### METHOD*: enum* *\= GPW*

**Usage:** *METHOD GAPW*

**Valid values:**

-   `GAPW` Gaussian and augmented plane waves method

-   `GAPW_XC` Gaussian and augmented plane waves method only for XC

-   `GPW` Gaussian and plane waves method

-   `LRIGPW` Local resolution of identity method

-   `RIGPW` Resolution of identity method for HXC terms

-   `MNDO` MNDO semiempirical

-   `MNDOD` MNDO-d semiempirical

-   `AM1` AM1 semiempirical

-   `PM3` PM3 semiempirical

-   `PM6` PM6 semiempirical

-   `PM6-FM` PM6-FM semiempirical

-   `PDG` PDG semiempirical

-   `RM1` RM1 semiempirical

-   `PNNL` PNNL semiempirical

-   `DFTB` DFTB Density Functional based Tight-Binding

-   `XTB` GFN-xTB Extended Tight-Binding

-   `OFGPW` OFGPW Orbital-free GPW method


**References:** [Lippert1997](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#lippert1997), [Lippert1999](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#lippert1999), [Krack2000](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#krack2000), [VandeVondele2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2005), [VandeVondele2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2006), [Dewar1977](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#dewar1977), [Dewar1985](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#dewar1985), [Rocha2006](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#rocha2006), [Stewart1989](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stewart1989), [Thiel1992](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#thiel1992), [Repasky2002](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#repasky2002), [Stewart2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#stewart2007), [VanVoorhis2015](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vanvoorhis2015), [Chang2008](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#chang2008)

**Mentions:** ⭐[X-Ray Absorption from TDDFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/tddft.html), ⭐[Extended Tight Binding](https://manual.cp2k.org/cp2k-2026_2-branch/methods/semiempiricals/xtb.html)

Specifies the electronic structure method that should be employed \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L466)\]

### MIN\_PAIR\_LIST\_RADIUS*: real* *\= 0.00000000E+000*

**Usage:** *MIN\_PAIR\_LIST\_RADIUS real*

Set the minimum value \[Bohr\] for the overlap pair list radius. Default is 0.0 Bohr, negative values are changed to the cell size. This allows to control the sparsity of the KS matrix for HFX calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L267)\]

### PW\_GRID*: enum* *\= NS-FULLSPACE*

**Usage:** *PW\_GRID NS-FULLSPACE*

**Valid values:**

-   `SPHERICAL`

    -   not tested

-   `NS-FULLSPACE` tested

-   `NS-HALFSPACE`

    -   not tested


What kind of PW\_GRID should be employed \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L383)\]

### PW\_GRID\_BLOCKED*: enum* *\= FREE*

**Usage:** *PW\_GRID\_BLOCKED FREE*

**Valid values:**

-   `FREE` CP2K will select an appropriate value

-   `TRUE` blocked

-   `FALSE` not blocked


Can be used to set the distribution in g-space for the pw grids and their FFT. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L404)\]

### PW\_GRID\_LAYOUT*: integer\[2\]* *\= \-1 \-1*

**Usage:** *PW\_GRID\_LAYOUT 4 16*

Force a particular real-space layout for the plane waves grids. Numbers ≤ 0 mean that this dimension is free, incorrect layouts will be ignored. The default (/-1,-1/) causes CP2K to select a good value, i.e. plane distributed for large grids, more general distribution for small grids. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L393)\]

### QUADRATURE*: enum* *\= GC\_LOG*

**Usage:** *QUADRATURE GC\_SIMPLE*

**Valid values:**

-   `GC_SIMPLE` Gauss-Chebyshev quadrature

-   `GC_TRANSFORMED` Transformed Gauss-Chebyshev quadrature

-   `GC_LOG` Logarithmic transformed Gauss-Chebyshev quadrature


GAPW: algorithm to construct the atomic radial grids \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L371)\]

### REF\_EMBED\_SUBSYS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *REF\_EMBED\_SUBSYS FALSE*

A total, reference, system in DFT embedding. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L304)\]

### STO\_NG*: integer* *\= 6*

**Usage:** *STO\_NG*

Order of Gaussian type expansion of Slater orbital basis sets. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L340)\]

### TRANSPORT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *TRANSPORT*

Perform transport calculations (coupling CP2K and OMEN) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_qs.F#L290)\]
