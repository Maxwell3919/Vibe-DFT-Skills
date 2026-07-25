# CP2K official manual snapshot: kind

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html
- Raw SHA-256: 213be6984fa2ce2cee4701b5c86a80e10f1efba526074e3cfb4d06f5df93e16e
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# KIND

**Section can be repeated.**

Defines settings shared by atoms of the same kind, such as basis sets, pseudopotentials, all-electron treatment, and atom-centered grids. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1085)\]

Subsections

-   [BASIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/BASIS.html)
-   [BS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/BS.html)
-   [DFT\_PLUS\_U](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html)
-   [KG\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/KG_POTENTIAL.html)
-   [PAO\_DESCRIPTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/PAO_DESCRIPTOR.html)
-   [PAO\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/PAO_POTENTIAL.html)
-   [POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/POTENTIAL.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.SECTION_PARAMETERS")

-   **[BASIS\_SET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.BASIS_SET "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.BASIS_SET")**

-   [CORE\_CORRECTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.CORE_CORRECTION "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.CORE_CORRECTION")

-   [COVALENT\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.COVALENT_RADIUS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.COVALENT_RADIUS")

-   [DFTB3\_PARAM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFTB3_PARAM "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFTB3_PARAM")

-   [ECP\_SEMI\_LOCAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ECP_SEMI_LOCAL "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ECP_SEMI_LOCAL")

-   [ELEC\_CONF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ELEC_CONF "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ELEC_CONF")

-   [ELEMENT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ELEMENT "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.ELEMENT")

-   [FLOATING\_BASIS\_CENTER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.FLOATING_BASIS_CENTER "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.FLOATING_BASIS_CENTER")

-   **[GHOST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.GHOST "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.GHOST")**

-   [GPW\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.GPW_TYPE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.GPW_TYPE")

-   [HARD\_EXP\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.HARD_EXP_RADIUS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.HARD_EXP_RADIUS")

-   [KG\_POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.KG_POTENTIAL "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.KG_POTENTIAL")

-   [KG\_POTENTIAL\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.KG_POTENTIAL_FILE_NAME "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.KG_POTENTIAL_FILE_NAME")

-   **[LEBEDEV\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.LEBEDEV_GRID "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.LEBEDEV_GRID")**

-   [LMAX\_DFTB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.LMAX_DFTB "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.LMAX_DFTB")

-   **[MAGNETIZATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAGNETIZATION "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAGNETIZATION")**

-   [MAO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAO "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAO")

-   [MASS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MASS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MASS")

-   [MAX\_RAD\_LOCAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAX_RAD_LOCAL "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MAX_RAD_LOCAL")

-   [MM\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MM_RADIUS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MM_RADIUS")

-   [MONOVALENT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MONOVALENT "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.MONOVALENT")

-   [NO\_OPTIMIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.NO_OPTIMIZE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.NO_OPTIMIZE")

-   **[PAO\_BASIS\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.PAO_BASIS_SIZE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.PAO_BASIS_SIZE")**

-   [PAO\_MODEL\_FILE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.PAO_MODEL_FILE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.PAO_MODEL_FILE")

-   **[POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL")**

-   [POTENTIAL\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_FILE_NAME "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_FILE_NAME")

-   [POTENTIAL\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_TYPE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_TYPE")

-   **[RADIAL\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.RADIAL_GRID "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.RADIAL_GRID")**

-   [RHO0\_EXP\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.RHO0_EXP_RADIUS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.RHO0_EXP_RADIUS")

-   [SE\_P\_ORBITALS\_ON\_H](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.SE_P_ORBITALS_ON_H "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.SE_P_ORBITALS_ON_H")

-   [VDW\_RADIUS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.VDW_RADIUS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.VDW_RADIUS")


## Keyword descriptions

### SECTION\_PARAMETERS*: string* *\= DEFAULT*

**Usage:** *H*

The name of the kind described in this section. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1092)\]

### BASIS\_SET*: string\[ \]*

**Keyword can be repeated.**

**Usage:** *BASIS\_SET \[type\] \[form\] DZVP*

**References:** [VandeVondele2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2005), [VandeVondele2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2007)

**Mentions:** ⭐[Basis Sets](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/basis_sets.html), ⭐[Band structure from GW](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/band/gw.html), ⭐[Preliminaries](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/preliminaries.html), ⭐[GW + Bethe-Salpeter equation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/bethe-salpeter.html)

Selects a Gaussian basis set for this kind. The default type is ORB and the default form is GTO; NONE implies no basis and is meaningful for ghost atoms. Possible values for TYPE are {ORB, AUX, MIN, RI\_AUX, LRI, …}. Possible values for FORM are {GTO, STO}. Where STO results in a GTO expansion of a Slater type basis. If a value for FORM is given, also TYPE has to be set explicitly. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1098)\]

### CORE\_CORRECTION*: real* *\= 0.00000000E+000*

**Usage:** *CORE\_CORRECTION 1.0*

Corrects the effective nuclear charge \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1166)\]

### COVALENT\_RADIUS*: real* *\= 0.00000000E+000 \[angstrom\]*

**Usage:** *COVALENT\_RADIUS 1.24*

Use this covalent radius (in Angstrom) for all atoms of the atomic kind instead of the internally tabulated default value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1246)\]

### DFTB3\_PARAM*: real* *\= 0.00000000E+000*

**Usage:** *DFTB3\_PARAM 0.2*

The third order parameter (derivative of hardness) used in diagonal DFTB3 correction. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1312)\]

### ECP\_SEMI\_LOCAL*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *ECP\_SEMI\_LOCAL {T,F}*

Use ECPs in the original semi-local form. This requires the availability of the corresponding integral library. If set to False, a fully nonlocal one-center expansion of the ECP is constructed. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1238)\]

### ELEC\_CONF*: integer\[ \]*

**Usage:** *ELEC\_CONF n\_elec(s) n\_elec(p) n\_elec(d) …*

Specifies the electronic configuration used in construction the atomic initial guess (see the pseudo potential file for the default values). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1158)\]

### ELEMENT*: string*

**Aliases:** ELEMENT\_SYMBOL

**Usage:** *ELEMENT O*

The element of the actual kind (if not given it is inferred from the kind name) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1181)\]

### FLOATING\_BASIS\_CENTER*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *FLOATING\_BASIS\_CENTER*

This keyword makes all atoms of this kind floating functions, i.e. without pseudo or nuclear charge which are subject to a geometry optimization in the outer SCF. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1370)\]

### GHOST*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *GHOST*

**Mentions:** ⭐[Preliminaries](https://manual.cp2k.org/cp2k-2026_2-branch/methods/post_hartree_fock/preliminaries.html)

This keyword makes all atoms of this kind ghost atoms, i.e. without pseudo or nuclear charge. Useful to just have the basis set at that position (e.g. BSSE calculations), or to have a non-interacting particle with BASIS\_SET NONE \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1347)\]

### GPW\_TYPE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *GPW\_TYPE*

Force one type to be treated by the GPW scheme, whatever are its primitives, even if the GAPW method is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1340)\]

### HARD\_EXP\_RADIUS*: real*

**Usage:** *HARD\_EXP\_RADIUS 0.9*

The region where the hard density is supposed to be confined (GAPW) (in Bohr, default is 1.2 for H and 1.512 otherwise) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1261)\]

### KG\_POTENTIAL*: string* *\= NONE*

**Aliases:** KG\_POT

**Usage:** *KG\_POTENTIAL*

The name of the non-additive atomic kinetic energy potential. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1231)\]

### KG\_POTENTIAL\_FILE\_NAME*: string* *\= \-*

**Usage:** *KG\_POTENTIAL\_FILE\_NAME*

The name of the file where to find this kinds KG potential. Default file is specified in DFT section. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1224)\]

### LEBEDEV\_GRID*: integer* *\= 50*

**Usage:** *LEBEDEV\_GRID 40*

**Mentions:** ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)

GAPW: size of the angular Lebedev grid used for atom-centered integrations for this kind. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1283)\]

### LMAX\_DFTB*: integer* *\= \-1*

**Usage:** *LMAX\_DFTB 1*

The maximum l-quantum number of the DFTB basis for this kind. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1319)\]

### MAGNETIZATION*: real* *\= 0.00000000E+000*

**Usage:** *MAGNETIZATION 0.5*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

The magnetization used in the atomic initial guess. Adds magnetization/2 spin-alpha electrons and removes magnetization/2 spin-beta electrons. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1173)\]

### MAO*: integer* *\= \-1*

**Usage:** *MAO 4*

The number of MAOs (Modified Atomic Orbitals) for this kind. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1325)\]

### MASS*: real*

**Aliases:** ATOMIC\_MASS ,ATOMIC\_WEIGHT ,WEIGHT

**Usage:** *MASS 2.0*

The mass of the atom (if negative or non present it is inferred from the element symbol) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1189)\]

### MAX\_RAD\_LOCAL*: real* *\= 2.45664397E+001*

**Usage:** *MAX\_RAD\_LOCAL 15.0*

Max radius for the basis functions used to generate the local projectors in GAPW \[Bohr\] \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1268)\]

### MM\_RADIUS*: real* *\= 0.00000000E+000 \[angstrom\]*

**Usage:** *MM\_RADIUS {real}*

Defines the radius of the electrostatic multipole of the atom in Fist. This radius applies to the charge, the dipole and the quadrupole. When zero, the atom is treated as a point multipole, otherwise it is treated as a Gaussian charge distribution with the given radius: p(x,y,z)*N*exp(-(x**2+y**2+z**2)/(2\*MM\_RADIUS**2)), where N is a normalization constant. In the core-shell model, only the shell is treated as a Gaussian and the core is always a point charge. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1297)\]

### MONOVALENT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *MONOVALENT*

This keyword makes all atoms of this kind monovalent, i.e. with a single electron and nuclear charge set to 1.0. Used to saturate dangling bonds, ideally in conjunction with a monovalent pseudopotential. Currently GTH only. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1359)\]

### NO\_OPTIMIZE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *NO\_OPTIMIZE*

Skip optimization of this type (used in specific basis set or potential optimization schemes) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1381)\]

### PAO\_BASIS\_SIZE*: integer* *\= 0*

**Mentions:** ⭐[PAO-ML](https://manual.cp2k.org/cp2k-2026_2-branch/methods/machine_learning/pao-ml.html)

The block size used for the polarized atomic orbital basis. Setting PAO\_BASIS\_SIZE to the size of the primary basis or to a value below one will disables the PAO method for the given atomic kind. By default PAO is disbabled. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1391)\]

### PAO\_MODEL\_FILE*: string*

The filename of the PyTorch model for predicting PAO basis sets. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1399)\]

### POTENTIAL*: string\[ \]*

**Aliases:** POT

**Usage:** *POTENTIAL \[type\]*

**References:** [Goedecker1996](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#goedecker1996), [Hartwigsen1998](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#hartwigsen1998), [Krack2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#krack2005)

**Mentions:** ⭐[Pseudopotentials](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/pseudopotentials.html)

The type (ECP, ALL, GTH, UPS) and name of the pseudopotential for the defined kind. Use GTH potentials for most GPW calculations, ECP for Gaussian-integral effective core potentials, and ALL for all-electron calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1211)\]

### POTENTIAL\_FILE\_NAME*: string* *\= \-*

**Usage:** *POTENTIAL\_FILE\_NAME*

The name of the file where to find this kinds pseudopotential. Default file is specified in DFT section. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1197)\]

### POTENTIAL\_TYPE*: string*

**Usage:** *POTENTIAL\_TYPE*

The type of this kinds pseudopotential (ECP, ALL, GTH, UPS). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1204)\]

Warning

The keyword [POTENTIAL\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_TYPE "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL_TYPE") is deprecated and may be removed in a future version.

Use ‘POTENTIAL …’ instead.

### RADIAL\_GRID*: integer* *\= 50*

**Usage:** *RADIAL\_GRID 70*

**Mentions:** ⭐[Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)

GAPW: number of radial grid points used for atom-centered integrations for this kind. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1290)\]

### RHO0\_EXP\_RADIUS*: real*

**Usage:** *RHO0\_EXP\_RADIUS 0.9*

the radius which defines the atomic region where the hard compensation density is confined. should be less than HARD\_EXP\_RADIUS (GAPW) (Bohr, default equals HARD\_EXP\_RADIUS) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1275)\]

### SE\_P\_ORBITALS\_ON\_H*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SE\_P\_ORBITALS\_ON\_H*

Forces the usage of p-orbitals on H for SEMI-EMPIRICAL calculations. This keyword applies only when the KIND is specifying an Hydrogen element. It is ignored in all other cases. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1332)\]

### VDW\_RADIUS*: real* *\= 0.00000000E+000 \[angstrom\]*

**Usage:** *VDW\_RADIUS 1.85*

Use this van der Waals radius (in Angstrom) for all atoms of the atomic kind instead of the internally tabulated default value \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1254)\]
