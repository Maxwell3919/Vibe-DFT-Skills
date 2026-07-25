# CP2K official manual snapshot: dft-plus-u

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html
- Raw SHA-256: a4c4ae9012870180fea370d0218d02bdff755e2ba614f79e94855bf7e7b3d5ff
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# DFT\_PLUS\_U

Define the parameters for a DFT+U run \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2370)\]

Subsections

-   [ENFORCE\_OCCUPATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U/ENFORCE_OCCUPATION.html)

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.SECTION_PARAMETERS")

-   [ALPHA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.ALPHA "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.ALPHA")

-   [BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.BETA "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.BETA")

-   [EPS\_U\_RAMPING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.EPS_U_RAMPING "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.EPS_U_RAMPING")

-   [INIT\_U\_RAMPING\_EACH\_SCF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.INIT_U_RAMPING_EACH_SCF "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.INIT_U_RAMPING_EACH_SCF")

-   [J](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.J "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.J")

-   [J0](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.J0 "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.J0")

-   [L](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.L "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.L")

-   [N](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.N "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.N")

-   [OCCUPATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.OCCUPATION "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.OCCUPATION")

-   [U](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U")

-   [U\_MINUS\_J](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U_MINUS_J "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U_MINUS_J")

-   [U\_RAMPING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U_RAMPING "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.DFT_PLUS_U.U_RAMPING")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&DFT\_PLUS\_U ON*

Controls the activation of the DFT+U section \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2378)\]

### ALPHA*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *alpha \[eV\] 1.4*

alpha parameter in the theory of Dudarev et al. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2448)\]

### BETA*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *beta \[eV\] 1.4*

beta parameter in the theory of Dudarev et al. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2460)\]

### EPS\_U\_RAMPING*: real* *\= 1.00000000E-005*

**Usage:** *EPS\_U\_RAMPING 1.0E-6*

Threshold value (SCF convergence) for incrementing the effective U value when U ramping is active. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2508)\]

### INIT\_U\_RAMPING\_EACH\_SCF*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *INIT\_U\_RAMPING\_EACH\_SCF on*

Set the initial U ramping value to zero before each wavefunction optimisation. The default is to apply U ramping only for the initial wavefunction optimisation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2520)\]

### J*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *J \[eV\] 1.4*

J parameter in the theory of Dudarev et al. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2436)\]

### J0*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *J0 \[eV\] 1.4*

J0 parameter in the theory of Dudarev et al. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2472)\]

### L*: integer* *\= \-1*

**Usage:** *L 2*

Angular momentum quantum number of the orbitals to which the correction is applied \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2387)\]

### N*: integer* *\= \-1*

**Usage:** *N 2*

principal quantum number of the orbitals to which the correction is applied. Ignored unless pwdft is used for the calculations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2412)\]

### OCCUPATION*: real* *\= 0.00000000E+000*

**Usage:** *occupation 6*

number of electrons in the hubbard shell. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2484)\]

### U*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *U \[eV\] 1.4*

U parameter in the theory of Dudarev et al. Ignored unless pwdft is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2424)\]

### U\_MINUS\_J*: real* *\= 0.00000000E+000 \[hartree\]*

**Aliases:** U\_EFF

**Usage:** *U\_MINUS\_J \[eV\] 1.4*

Effective parameter U(eff) = U - J \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2399)\]

### U\_RAMPING*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *U\_RAMPING \[eV\] 0.1*

Increase the effective U parameter stepwise using the specified increment until the target value given by U\_MINUS\_J is reached. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2495)\]
