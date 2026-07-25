# CP2K official manual snapshot: dft

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html
- Raw SHA-256: 3b882b74509d0ba7dd7984bebbe2ceef3d00bc24d42460727842c25c466824fb
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# DFT

Controls electronic-structure settings for Quickstep and related Gaussian-basis DFT methods. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L128)\]

Subsections

-   [ACTIVE\_SPACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/ACTIVE_SPACE.html)
-   [ALMO\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/ALMO_SCF.html)
-   [AUXILIARY\_DENSITY\_MATRIX\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html)
-   [DENSITY\_FITTING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/DENSITY_FITTING.html)
-   [EFIELD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/EFIELD.html)
-   [ENERGY\_CORRECTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/ENERGY_CORRECTION.html)
-   [EXCITED\_STATES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/EXCITED_STATES.html)
-   [EXTERNAL\_DENSITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/EXTERNAL_DENSITY.html)
-   [EXTERNAL\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/EXTERNAL_POTENTIAL.html)
-   [EXTERNAL\_VXC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/EXTERNAL_VXC.html)
-   [HAIRY\_PROBES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/HAIRY_PROBES.html)
-   [HARRIS\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/HARRIS_METHOD.html)
-   [KG\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KG_METHOD.html)
-   [KPOINTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html)
-   [KPOINT\_SET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINT_SET.html)
-   [LOCALIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/LOCALIZE.html)
-   [LOW\_SPIN\_ROKS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/LOW_SPIN_ROKS.html)
-   [LS\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/LS_SCF.html)
-   [MGRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html)
-   [PERIODIC\_EFIELD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PERIODIC_EFIELD.html)
-   [PLANAR\_AVERAGED\_V\_HARTREE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PLANAR_AVERAGED_V_HARTREE.html)
-   [PLANAR\_COUNTER\_CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PLANAR_COUNTER_CHARGE.html)
-   [POISSON](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT.html)
-   [QS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html)
-   [REAL\_TIME\_PROPAGATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html)
-   [RELATIVISTIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/RELATIVISTIC.html)
-   [SCCS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html)
-   [SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html)
-   [SCRF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCRF.html)
-   [SIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SIC.html)
-   [SMEAGOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SMEAGOL.html)
-   [TRANSPORT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html)
-   [XAS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html)
-   [XAS\_TDP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS_TDP.html)
-   [XC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html)

## Keywords

-   **[AUTO\_BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.AUTO_BASIS "CP2K_INPUT.FORCE_EVAL.DFT.AUTO_BASIS")**

-   **[BASIS\_SET\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.BASIS_SET_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.BASIS_SET_FILE_NAME")**

-   **[CHARGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.CHARGE "CP2K_INPUT.FORCE_EVAL.DFT.CHARGE")**

-   [CORE\_CORR\_DIP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.CORE_CORR_DIP "CP2K_INPUT.FORCE_EVAL.DFT.CORE_CORR_DIP")

-   **[MULTIPLICITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.MULTIPLICITY "CP2K_INPUT.FORCE_EVAL.DFT.MULTIPLICITY")**

-   [PLUS\_U\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.PLUS_U_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.PLUS_U_METHOD")

-   **[POTENTIAL\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.POTENTIAL_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.POTENTIAL_FILE_NAME")**

-   [RELAX\_MULTIPLICITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.RELAX_MULTIPLICITY "CP2K_INPUT.FORCE_EVAL.DFT.RELAX_MULTIPLICITY")

-   [ROKS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.ROKS "CP2K_INPUT.FORCE_EVAL.DFT.ROKS")

-   **[SORT\_BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SORT_BASIS "CP2K_INPUT.FORCE_EVAL.DFT.SORT_BASIS")**

-   [SUBCELLS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SUBCELLS "CP2K_INPUT.FORCE_EVAL.DFT.SUBCELLS")

-   [SURFACE\_DIPOLE\_CORRECTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SURFACE_DIPOLE_CORRECTION "CP2K_INPUT.FORCE_EVAL.DFT.SURFACE_DIPOLE_CORRECTION")

-   [SURF\_DIP\_DIR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_DIR "CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_DIR")

-   [SURF\_DIP\_POS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_POS "CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_POS")

-   [SURF\_DIP\_SWITCH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_SWITCH "CP2K_INPUT.FORCE_EVAL.DFT.SURF_DIP_SWITCH")

-   **[UKS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.UKS "CP2K_INPUT.FORCE_EVAL.DFT.UKS")**

-   **[WFN\_RESTART\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.WFN_RESTART_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.WFN_RESTART_FILE_NAME")**


## Keyword descriptions

### AUTO\_BASIS*: string\[ \]* *\= X X*

**Keyword can be repeated.**

**Usage:** *AUTO\_BASIS {basis\_type} {basis\_size}*

**Mentions:** ⭐[Preliminaries](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/preliminaries.html), ⭐[X-Ray Absorption from TDDFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/tddft.html)

Specify size of automatically generated auxiliary (RI) basis sets: Options={small,medium,large,huge} \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L252)\]

### BASIS\_SET\_FILE\_NAME*: string* *\= BASIS\_SET*

**Keyword can be repeated.**

**Usage:** *BASIS\_SET\_FILE\_NAME*

**Mentions:** ⭐[Basis Sets](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/basis_sets.html)

Name of a basis-set library file, optionally including a path. This keyword can be repeated to search several basis-set files. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L134)\]

### CHARGE*: integer* *\= 0*

**Usage:** *CHARGE -1*

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html), ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[RESP Charges](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/population/resp.html)

The total charge of the system \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L193)\]

### CORE\_CORR\_DIP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *CORE\_CORR\_DIP .TRUE.*

If the total CORE\_CORRECTION is non-zero and surface dipole correction is switched on, presence of this keyword will adjust electron density via MO occupation to reflect the total CORE\_CORRECTION. The default value is .FALSE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L311)\]

### MULTIPLICITY*: integer* *\= 0*

**Aliases:** MULTIP

**Usage:** *MULTIPLICITY 3*

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html), ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Two times the total spin plus one. Specify 3 for a triplet, 4 for a quartet, and so on. Default is 1 (singlet) for an even number and 2 (doublet) for an odd number of electrons. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L181)\]

### PLUS\_U\_METHOD*: enum* *\= MULLIKEN*

**Usage:** *PLUS\_U\_METHOD Lowdin*

**Valid values:**

-   `LOWDIN` Method based on Lowdin population analysis (computationally expensive, since the diagonalization of the overlap matrix is required, but possibly more robust than Mulliken)

-   `MULLIKEN` Method based on Mulliken population analysis using the net AO and overlap populations (computationally cheap method)

-   `MULLIKEN_CHARGES` Method based on Mulliken gross orbital populations (GOP)


Method employed for the calculation of the DFT+U contribution \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L200)\]

### POTENTIAL\_FILE\_NAME*: string* *\= POTENTIAL*

**Usage:** *POTENTIAL\_FILE\_NAME*

**Mentions:** ⭐[Pseudopotentials](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/pseudopotentials.html)

Name of the pseudopotential library file, optionally including a path. The potential selected for each kind is set with KIND%POTENTIAL. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L143)\]

### RELAX\_MULTIPLICITY*: real* *\= 0.00000000E+000*

**Aliases:** RELAX\_MULTIP

**Usage:** *RELAX\_MULTIPLICITY 0.00001*

Tolerance in Hartrees. Do not enforce the occupation of alpha and beta MOs due to the initially defined multiplicity, but rather follow the Aufbau principle. A value greater than zero activates this option. If alpha/beta MOs differ in energy less than this tolerance, then alpha-MO occupation is preferred even if it is higher in energy (within the tolerance). Such spin-symmetry broken (spin-polarized) occupation is used as SCF input, which (is assumed to) bias the SCF towards a spin-polarized solution. Thus, larger tolerance increases chances of ending up with spin-polarization. This option is only valid for unrestricted (i.e. spin polarised) Kohn-Sham (UKS) calculations. It also needs non-zero [ADDED\_MOS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.ADDED_MOS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.ADDED_MOS") to actually affect the calculations, which is why it is not expected to work with [OT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OT.html#cp2k-input-force-eval-dft-scf-ot) and may raise errors when used with OT. For more details see [this discussion](https://github.com/cp2k/cp2k/issues/4389). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L218)\]

### ROKS*: logical* *\= F*

**Aliases:** RESTRICTED\_OPEN\_KOHN\_SHAM

**Lone keyword:** `T`

**Usage:** *ROKS*

Requests a restricted open Kohn-Sham calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L172)\]

### SORT\_BASIS*: enum* *\= DEFAULT*

**Usage:** *SORT\_BASIS EXP*

**Valid values:**

-   `DEFAULT` don’t sort

-   `EXP` sort w.r.t. exponent


**Mentions:** ⭐[HFX-RI for Γ-Point (non-periodic)](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/ri_gamma.html)

Sorts basis functions according to a selected criterion. Sorting by exponent can improve data locality for selected exact-exchange and RI workflows. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L323)\]

### SUBCELLS*: real* *\= 2.00000000E+000*

**Usage:** *SUBCELLS 1.5*

Read the grid size for subcell generation in the construction of neighbor lists. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L245)\]

### SURFACE\_DIPOLE\_CORRECTION*: logical* *\= F*

**Aliases:** SURFACE\_DIPOLE ,SURF\_DIP

**Lone keyword:** `T`

**Usage:** *SURF\_DIP*

**References:** [Bengtsson1999](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#bengtsson1999)

For slab calculations with asymmetric geometries, activate the correction of the electrostatic potential with by compensating for the surface dipole. Implemented only for slabs with normal parallel to one Cartesian axis. The normal direction is given by the keyword SURF\_DIP\_DIR \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L260)\]

### SURF\_DIP\_DIR*: enum* *\= Z*

**Usage:** *SURF\_DIP\_DIR Z*

**Valid values:**

-   `X` Along x

-   `Y` Along y

-   `Z` Along z


Cartesian axis parallel to surface normal. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L275)\]

### SURF\_DIP\_POS*: real* *\= \-1.00000000E+000*

**Usage:** *SURF\_DIP\_POS -1.0\_dp*

This keyword assigns an user defined position in Angstroms in the direction normal to the surface (given by SURF\_DIP\_DIR). The default value is -1.0\_dp which appplies the correction at a position that has minimum electron density on the grid. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L287)\]

### SURF\_DIP\_SWITCH*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SURF\_DIP\_SWITCH .TRUE.*

WARNING: Experimental feature under development that will help the user to switch parameters to facilitate SCF convergence. In its current form the surface dipole correction is switched off if the calculation does not converge in (0.5\*MAX\_SCF + 1) outer\_scf steps. The default value is .FALSE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L298)\]

### UKS*: logical* *\= F*

**Aliases:** UNRESTRICTED\_KOHN\_SHAM ,LSD ,SPIN\_POLARIZED

**Lone keyword:** `T`

**Usage:** *LSD*

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html), ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Extended Tight Binding](https://manual.cp2k.org/cp2k-2026_2-branch/methods/semiempiricals/xtb.html)

Requests a spin-polarized calculation using alpha and beta orbitals, i.e. no spin restriction is applied \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L160)\]

### WFN\_RESTART\_FILE\_NAME*: string*

**Aliases:** RESTART\_FILE\_NAME

**Usage:** *WFN\_RESTART\_FILE\_NAME*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

Name of the wavefunction restart file, may include a path. If no file is specified, the default is to open the file as generated by the wfn restart print key. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L151)\]
