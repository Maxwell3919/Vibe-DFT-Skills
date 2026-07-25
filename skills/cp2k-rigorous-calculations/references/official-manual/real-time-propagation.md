# CP2K official manual snapshot: real-time-propagation

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html
- Raw SHA-256: 19c42ffd401ce0de2b765f95124eaf86fd5cf18b5be75a777b9362c54aca2a32
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# REAL\_TIME\_PROPAGATION

**References:** [Kunert2003](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#kunert2003), [Andermatt2016](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#andermatt2016)

Parameters needed to set up the real time propagation for the electron dynamics. This currently works only in the NVE ensemble. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1550)\]

Subsections

-   [FT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION/FT.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION/PRINT.html)
-   [RTBSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION/RTBSE.html)

## Keywords

-   [ACCURACY\_REFINEMENT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.ACCURACY_REFINEMENT "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.ACCURACY_REFINEMENT")

-   **[APPLY\_DELTA\_PULSE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_DELTA_PULSE "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_DELTA_PULSE")**

-   [APPLY\_DELTA\_PULSE\_MAG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_DELTA_PULSE_MAG "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_DELTA_PULSE_MAG")

-   [APPLY\_WFN\_MIX\_INIT\_RESTART](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_WFN_MIX_INIT_RESTART "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.APPLY_WFN_MIX_INIT_RESTART")

-   [ASPC\_ORDER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.ASPC_ORDER "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.ASPC_ORDER")

-   [COM\_NL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.COM_NL "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.COM_NL")

-   **[DELTA\_PULSE\_DIRECTION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DELTA_PULSE_DIRECTION "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DELTA_PULSE_DIRECTION")**

-   **[DELTA\_PULSE\_SCALE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DELTA_PULSE_SCALE "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DELTA_PULSE_SCALE")**

-   **[DENSITY\_PROPAGATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DENSITY_PROPAGATION "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.DENSITY_PROPAGATION")**

-   **[EPS\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.EPS_ITER "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.EPS_ITER")**

-   **[EXP\_ACCURACY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.EXP_ACCURACY "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.EXP_ACCURACY")**

-   [GAUGE\_ORIG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.GAUGE_ORIG "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.GAUGE_ORIG")

-   [GAUGE\_ORIG\_MANUAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.GAUGE_ORIG_MANUAL "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.GAUGE_ORIG_MANUAL")

-   [HFX\_BALANCE\_IN\_CORE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.HFX_BALANCE_IN_CORE "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.HFX_BALANCE_IN_CORE")

-   **[INITIAL\_WFN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.INITIAL_WFN "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.INITIAL_WFN")**

-   [LEN\_REP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.LEN_REP "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.LEN_REP")

-   [LOCALIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.LOCALIZE "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.LOCALIZE")

-   **[MAT\_EXP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MAT_EXP "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MAT_EXP")**

-   **[MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MAX_ITER "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MAX_ITER")**

-   [MCWEENY\_EPS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MCWEENY_EPS "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MCWEENY_EPS")

-   [MCWEENY\_MAX\_ITER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MCWEENY_MAX_ITER "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.MCWEENY_MAX_ITER")

-   **[PERIODIC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.PERIODIC "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.PERIODIC")**

-   [PROPAGATOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.PROPAGATOR "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.PROPAGATOR")

-   [SC\_CHECK\_START](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.SC_CHECK_START "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.SC_CHECK_START")

-   [VELOCITY\_GAUGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.VELOCITY_GAUGE "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.VELOCITY_GAUGE")

-   [VG\_COM\_NL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html#CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.VG_COM_NL "CP2K_INPUT.FORCE_EVAL.DFT.REAL_TIME_PROPAGATION.VG_COM_NL")


## Keyword descriptions

### ACCURACY\_REFINEMENT*: integer* *\= 100*

**Usage:** *ACCURACY\_REFINEMENT*

If using density propagation some parts should be calculated with a higher accuracy than the rest to reduce numerical noise. This factor determines by how much the filtering threshold is reduced for these calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1792)\]

### APPLY\_DELTA\_PULSE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *APPLY\_DELTA\_PULSE*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html)

Applies a delta kick to the initial wfn (only RTP for now - the EMD case is not yet implemented). Only work for INITIAL\_WFN=SCF\_WFN \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1662)\]

### APPLY\_DELTA\_PULSE\_MAG*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *APPLY\_DELTA\_PULSE\_MAG*

Applies a magnetic delta kick to the initial wfn (only RTP for now - the EMD case is not yet implemented). Only work for INITIAL\_WFN=SCF\_WFN \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1670)\]

### APPLY\_WFN\_MIX\_INIT\_RESTART*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *APPLY\_WFN\_MIX\_INIT\_RESTART*

If set to True and in the case of INITIAL\_WFN=RESTART\_WFN, call the DFT%PRINT%WFN\_MIX section to mix the read initial wfn. The starting wave-function of the RTP will be the mixed one. Setting this to True without a defined WFN\_MIX section will not do anything as defining a WFN\_MIX section without this keyword for RTP run with INITIAL\_WFN=RESTART\_WFN. Note that if INITIAL\_WFN=SCF\_WFN, this keyword is not needed to apply the mixing defined in the WFN\_MIX section. Default is False. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1650)\]

### ASPC\_ORDER*: integer* *\= 3*

**Usage:** *ASPC\_ORDER 3*

Speciefies how many steps will be used for extrapolation. One will be always used which is means X(t+dt)=X(t) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1570)\]

### COM\_NL*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *COM\_NL*

Include non-local commutator for periodic delta pulse. only affects PERIODIC=.TRUE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1721)\]

### DELTA\_PULSE\_DIRECTION*: integer\[3\]* *\= 1 0 0*

**Usage:** *DELTA\_PULSE\_DIRECTION 1 1 1*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[X-Ray Absorption from RTP and \\delta-Kick perturbation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/delta-kick.html)

Direction of the applied electric field. The k vector is given as 2*Pi*\[i,j,k\]*inv(h\_mat), which for PERIODIC .FALSE. yields exp(ikr) periodic with the unit cell, only if DELTA\_PULSE\_SCALE is set to unity. For an orthorhombic cell \[1,0,0\] yields \[2*Pi/L\_x,0,0\]. For small cells, this results in a very large kick. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1758)\]

### DELTA\_PULSE\_SCALE*: real* *\= 1.00000000E-003*

**Usage:** *DELTA\_PULSE\_SCALE 0.01*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[X-Ray Absorption from RTP and \\delta-Kick perturbation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/delta-kick.html)

Scale the k vector, which for PERIODIC .FALSE. results in exp(ikr) no longer being periodic with the unit cell. The norm of k is the strength of the applied electric field in atomic units. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1768)\]

### DENSITY\_PROPAGATION*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DENSITY\_PROPAGATION .TRUE.*

**Mentions:** ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

The density matrix is propagated instead of the molecular orbitals. This can allow a linear scaling simulation. The density matrix is filtered with the threshold based on the EPS\_FILTER keyword from the LS\_SCF section \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1597)\]

### EPS\_ITER*: real* *\= 1.00000000E-007*

**Usage:** *EPS\_ITER 1.0E-5*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

Convergence criterion for the self consistent propagator loop. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1563)\]

### EXP\_ACCURACY*: real* *\= 1.00000000E-009*

**Usage:** *EXP\_ACCURACY 1.0E-6*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html)

Accuracy for the taylor and pade approximation. This is only an upper bound bound since the norm used for the guess is an upper bound for the needed one. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1614)\]

### GAUGE\_ORIG*: enum* *\= COM*

**Usage:** *GAUGE\_ORIG COM*

**Valid values:**

-   `COM` Use Center of Mass

-   `COAC` Use Center of Atomic Charges

-   `USER_DEFINED` Use User Defined Point (Keyword:REF\_POINT)

-   `ZERO` Use Origin of Coordinate System


Define gauge origin for magnetic perturbation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1687)\]

### GAUGE\_ORIG\_MANUAL*: real\[3\]* *\= 0.00000000E+000 0.00000000E+000 0.00000000E+000 \[bohr\]*

**Usage:** *GAUGE\_ORIG\_MANUAL x y z*

Manually defined gauge origin for magnetic perturbation \[in Bohr!\] \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1703)\]

### HFX\_BALANCE\_IN\_CORE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *HFX\_BALANCE\_IN\_CORE*

If HFX is used, this keyword forces a redistribution/recalculation of the integrals, balanced with respect to the in core steps. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1776)\]

### INITIAL\_WFN*: enum* *\= SCF\_WFN*

**Usage:** *INITIAL\_WFN SCF\_WFN*

**Valid values:**

-   `SCF_WFN` An SCF run is performed to get the initial state.

-   `RESTART_WFN` A wavefunction from a previous SCF is propagated. Especially useful, if electronic constraints or restraints are used in the previous calculation, since these do not work in the rtp scheme.

-   `RT_RESTART` use the wavefunction of a real time propagation/ehrenfest run


**Mentions:** ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

Controls the initial WFN used for propagation. Note that some energy contributions may not be initialized in the restart cases, for instance electronic entropy energy in the case of smearing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1634)\]

### LEN\_REP*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *LEN\_REP T*

Use length representation delta pulse (in conjunction with PERIODIC T). This corresponds to a 1st order perturbation in the length gauge. Note that this is NOT compatible with a periodic calculation! Uses the reference point defined in DFT%PRINT%MOMENTS \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1729)\]

### LOCALIZE*: integer* *\= 0*

**Usage:** *LOCALIZE*

Localise the Molecular orbitals each n steps real-time propagated TDDFT, 0 means never localise \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1751)\]

### MAT\_EXP*: enum* *\= ARNOLDI*

**Usage:** *MAT\_EXP TAYLOR*

**Valid values:**

-   `TAYLOR` exponential is evaluated using scaling and squaring in combination with a taylor expansion of the exponential.

-   `PADE` uses scaling and squaring together with the pade approximation

-   `ARNOLDI` uses arnoldi subspace algorithm to compute exp(H)\*MO directly, can’t be used in combination with Crank Nicholson or density propagation

-   `BCH` Uses a Baker-Campbell-Hausdorff expansion to propagate the density matrix, only works for density propagation

-   `EXACT` Uses diagonalisation of the exponent matrices to determine the matrix exponential exactly. Only implemented for GWBSE.


**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

Which method should be used to calculate the exponential in the propagator. It is recommended to use BCH when employing density\_propagation and ARNOLDI otherwise. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1578)\]

### MAX\_ITER*: integer* *\= 10*

**Usage:** *MAX\_ITER 10*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

Maximal number of iterations for the self consistent propagator loop. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1556)\]

### MCWEENY\_EPS*: real* *\= 0.00000000E+000*

**Usage:** *MCWEENY\_EPS 0.00001*

Threshold after which McWeeny is terminated \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1800)\]

### MCWEENY\_MAX\_ITER*: integer* *\= 1*

**Usage:** *MCWEENY\_MAX\_ITER 2*

Determines the maximum amount of McWeeny steps used after each converged step in density propagation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1784)\]

### PERIODIC*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *PERIODIC*

**Mentions:** ⭐[X-Ray Absorption from RTP and \\delta-Kick perturbation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/delta-kick.html)

Apply a delta-kick that is compatible with periodic boundary conditions for any value of DELTA\_PULSE\_SCALE. Uses perturbation theory for the preparation of the initial wfn with the velocity operator as perturbation. If LEN\_REP is .FALSE. this corresponds to a first order velocity gauge. Note that the pulse is only applied when INITIAL\_WFN is set to SCF\_WFN, and not for restarts (RT\_RESTART). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1739)\]

### PROPAGATOR*: enum* *\= ETRS*

**Usage:** *PROPAGATOR ETRS*

**Valid values:**

-   `ETRS` enforced time reversible symmetry

-   `CN` Crank Nicholson propagator

-   `EM` Exponential midpoint propagator


Which propagator should be used for the orbitals \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1623)\]

### SC\_CHECK\_START*: integer* *\= 0*

**Usage:** *SC\_CHECK\_START 3*

Speciefies how many iteration steps will be done without a check for self consistency. Can save some time in big calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1606)\]

### VELOCITY\_GAUGE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *VELOCITY\_GAUGE T*

Perform propagation in the velocity gauge using the explicit vector potential only a constant vector potential as of now (corresonding to a delta-pulse). uses DELTA\_PULSE\_SCALE and DELTA\_PULSE\_DIRECTION to define the vector potential \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1678)\]

### VG\_COM\_NL*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *VG\_COM\_NL T*

apply gauge transformed non-local potential term only affects VELOCITY\_GAUGE=.TRUE. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_dft.F#L1713)\]
