# CP2K official manual snapshot: scf-mixing

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html
- Raw SHA-256: 18b2772c8d76564fa4ace05fa597455a3643cfaabd80ed972543012b793ac3f0
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# MIXING

Define type and parameters for mixing procedures to be applied to the density matrix. Normally, only one type of mixing method should be accepted. The mixing procedures activated by this section are only active for diagonalization methods and linear scaling SCF, i.e. not with minimization methods based on OT. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L513)\]

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.SECTION_PARAMETERS")

-   [ALPHA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.ALPHA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.ALPHA")

-   [ALPHA\_MAG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.ALPHA_MAG "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.ALPHA_MAG")

-   [BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BETA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BETA")

-   [BETA\_MAG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BETA_MAG "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BETA_MAG")

-   [BROY\_W0](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_W0 "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_W0")

-   [BROY\_WMAX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_WMAX "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_WMAX")

-   [BROY\_WREF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_WREF "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.BROY_WREF")

-   [GMIX\_P](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.GMIX_P "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.GMIX_P")

-   [MAX\_GVEC\_EXP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.MAX_GVEC_EXP "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.MAX_GVEC_EXP")

-   [MAX\_STEP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.MAX_STEP "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.MAX_STEP")

-   **[METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.METHOD")**

-   [NBUFFER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NBUFFER "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NBUFFER")

-   [NMIXING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NMIXING "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NMIXING")

-   [NSKIP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NSKIP "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.NSKIP")

-   [N\_SIMPLE\_MIX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.N_SIMPLE_MIX "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.N_SIMPLE_MIX")

-   [PULAY\_ALPHA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.PULAY_ALPHA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.PULAY_ALPHA")

-   [PULAY\_BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.PULAY_BETA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.PULAY_BETA")

-   [QK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QK "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QK")

-   [QKAPPA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QKAPPA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QKAPPA")

-   [QM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QM "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.QM")

-   [REGULARIZATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.REGULARIZATION "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.REGULARIZATION")

-   [R\_FACTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.R_FACTOR "CP2K_INPUT.FORCE_EVAL.DFT.SCF.MIXING.R_FACTOR")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *&MIXING ON*

Controls the activation of the mixing procedure \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L527)\]

### ALPHA*: real* *\= 4.00000000E-001*

**Usage:** *ALPHA 0.2*

Fraction of new density to be included \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L573)\]

### ALPHA\_MAG*: real* *\= \-1.00000000E+000*

**Usage:** *ALPHA\_MAG 0.8*

Fraction of new magnetization density to be included (for spin-polarized calculations, ispin=2 channel after rho\_total/m transform). A negative value (default) means: use the same value as ALPHA. For magnetic transition-metal systems, a larger value (e.g. 0.8-1.6) than ALPHA often improves convergence. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L584)\]

### BETA*: real* *\= 5.00000000E-001 \[bohr^-1\]*

**Usage:** *BETA 1.5*

Denominator parameter in Kerker damping introduced to suppress charge sloshing: rho\_mix(g) = rho\_in(g) + alpha*g^2/(g^2 + beta^2)*(rho\_out(g)-rho\_in(g)) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L599)\]

### BETA\_MAG*: real* *\= \-1.00000000E+000 \[bohr^-1\]*

**Usage:** *BETA\_MAG 0.0*

Kerker damping parameter for the magnetization channel (for spin-polarized calculations). A negative value (default) means: use the same value as BETA. Set to 0.0 to disable Kerker screening on the magnetization density, which avoids suppression of long-range magnetic order formation in transition-metal systems. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L613)\]

### BROY\_W0*: real* *\= 1.00000000E-002*

**Usage:** *BROY\_W0 0.03*

Regularization weight used in Broyden mixing. For the original BROYDEN\_MIXING method this is the constant diagonal regularization of the small Broyden system. For MODIFIED\_BROYDEN\_MIXING it is the corresponding diagonal regularization of the dynamically weighted Broyden system. The default follows tblite. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L708)\]

### BROY\_WMAX*: real* *\= 1.00000000E+005*

**Usage:** *BROY\_WMAX 100000.0*

Upper bound for the dynamic residual weight. This keyword is only used by MODIFIED\_BROYDEN\_MIXING; the original BROYDEN\_MIXING path is unchanged. The lower bound is fixed to 1.0. The default follows tblite. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L738)\]

### BROY\_WREF*: real* *\= 1.00000000E-002*

**Usage:** *BROY\_WREF 0.01*

Reference factor for the dynamic residual weight. This keyword is only used by MODIFIED\_BROYDEN\_MIXING; the original BROYDEN\_MIXING path is unchanged. The effective history weight is proportional to BROY\_WREF divided by the residual norm, clipped to the interval \[1, BROY\_WMAX\]. The default follows tblite. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L723)\]

### GMIX\_P*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *GMIX\_P*

Activate the mixing of the density matrix, using the same mixing coefficient applied for the g-space mixing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L816)\]

### MAX\_GVEC\_EXP*: real* *\= \-1.00000000E+000*

**Usage:** *MAX\_GVEC\_EXP 3.*

Restricts the G-space mixing to lower part of G-vector spectrum, up to a G0, by assigning the exponent of the Gaussian that can be represented by vectors smaller than G0 within a certain accuracy. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L804)\]

### MAX\_STEP*: real* *\= 1.00000000E-001*

**Usage:** *MAX\_STEP .2*

Upper bound for the magnitude of the unpredicted step size in the update by the multisecant mixing scheme \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L764)\]

### METHOD*: enum* *\= DIRECT\_P\_MIXING*

**Usage:** *METHOD KERKER\_MIXING*

**Valid values:**

-   `NONE` No mixing is applied

-   `DIRECT_P_MIXING` Direct mixing of new and old density matrices

-   `KERKER_MIXING` Mixing of the potential in reciprocal space using the Kerker damping

-   `PULAY_MIXING` Pulay mixing

-   `BROYDEN_MIXING` Original CP2K Broyden mixing with a constant BROY\_W0 regularization

-   `MODIFIED_BROYDEN_MIXING` Modified Broyden mixing with dynamic residual weights controlled by BROY\_W0, BROY\_WREF, and BROY\_WMAX

-   `MULTISECANT_MIXING` Multisecant scheme for mixing

-   `NEW_PULAY_MIXING` New Pulay mixing using Sundararaman et al.’s metric and preconditioner, with improved convergence behavior and suitable for grand canonical SCF


**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Mixing method to be applied \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L542)\]

### NBUFFER*: integer* *\= 4*

**Aliases:** NPULAY ,NBROYDEN ,NMULTISECANT

**Usage:** *NBUFFER 2*

Number of previous steps stored for the actual mixing scheme \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L701)\]

### NMIXING*: integer* *\= 2*

**Usage:** *NMIXING 1*

Minimal number of density mixing (should be greater than 0), before starting DIIS \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L694)\]

### NSKIP*: integer* *\= 0*

**Aliases:** NSKIP\_MIXING

**Usage:** *NSKIP 10*

Number of initial iteration for which the mixing is skipped \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L790)\]

### N\_SIMPLE\_MIX*: integer* *\= 0*

**Aliases:** NSIMPLEMIX

**Usage:** *NSIMPLEMIX*

Number of kerker damping iterations before starting other mixing procedures \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L797)\]

### PULAY\_ALPHA*: real* *\= 0.00000000E+000*

**Usage:** *PULAY\_ALPHA 0.2*

Fraction of new density to be added to the Pulay expansion \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L629)\]

### PULAY\_BETA*: real* *\= 1.00000000E+000*

**Usage:** *PULAY\_BETA 0.2*

Fraction of residual contribution to be added to Pulay expansion \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L640)\]

### QK*: real* *\= 3.00000000E+000 \[bohr^-1\]*

**Usage:** *QK 3.0*

The control parameter in the denominator of the Kerker preconditioner used in the new Pulay mixing, introduced to suppress charge sloshing: Kerker preconditioner: K(g) = alpha \* (g^2 + qkapa^2)/(g^2 + qk^2 + qkapa^2) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L665)\]

### QKAPPA*: real* *\= 2.50000000E-001 \[bohr^-1\]*

**Usage:** *QKAPPA 0.25*

The control parameter in the numerator and the denominator of the Pulay metric and the Kerker preconditioner used in the new Pulay mixing, introduced to ensure a finite and well-defined Pulay metric at g=0 and a non-zero and well-defined Kerker preconditioner at g=0 \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L679)\]

### QM*: real* *\= 7.50000000E-001 \[bohr^-1\]*

**Usage:** *QM 0.75*

The control parameter in the numerator of the Pulay metric used in the new Pulay mixing, introduced to suppress charge sloshing: Pulay metric: M(g) = (g^2 + qm^2 + qkapa^2)/(g^2 + qkapa^2) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L651)\]

### REGULARIZATION*: real* *\= 1.00000000E-005*

**Usage:** *REGULARIZATION 0.000001*

Regularization parameter to stabilize the inversion of the residual matrix {Yn^t Yn} in the multisecant mixing scheme (noise) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L751)\]

### R\_FACTOR*: real* *\= 5.00000000E-002*

**Usage:** *R\_FACTOR .12*

Control factor for the magnitude of the unpredicted step size in the update by the multisecant mixing scheme \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/qs_density_mixing_types.F#L777)\]
