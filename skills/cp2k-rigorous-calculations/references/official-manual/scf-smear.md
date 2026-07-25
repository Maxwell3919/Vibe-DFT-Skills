# CP2K official manual snapshot: scf-smear

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html
- Raw SHA-256: 7d20eb39a1bcc0d41ad7ee8fdc0f4832f017e2961f956c20596d891fa94775f3
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# SMEAR

Controls smearing of MO occupation numbers for systems with small or zero gaps. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1265)\]

## Keywords

-   [SECTION\_PARAMETERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.SECTION_PARAMETERS "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.SECTION_PARAMETERS")

-   **[ELECTRONIC\_TEMPERATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.ELECTRONIC_TEMPERATURE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.ELECTRONIC_TEMPERATURE")**

-   [EPS\_FERMI\_DIRAC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.EPS_FERMI_DIRAC "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.EPS_FERMI_DIRAC")

-   [FIXED\_MAGNETIC\_MOMENT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.FIXED_MAGNETIC_MOMENT "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.FIXED_MAGNETIC_MOMENT")

-   [LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.LIST "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.LIST")

-   **[METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.METHOD "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.METHOD")**

-   **[SIGMA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.SIGMA "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.SIGMA")**

-   [WINDOW\_SIZE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/SMEAR.html#CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.WINDOW_SIZE "CP2K_INPUT.FORCE_EVAL.DFT.SCF.SMEAR.WINDOW_SIZE")


## Keyword descriptions

### SECTION\_PARAMETERS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *&SMEAR ON*

Controls the activation of smearing \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1274)\]

### ELECTRONIC\_TEMPERATURE*: real* *\= 3.00000000E+002 \[K\]*

**Aliases:** ELEC\_TEMP ,TELEC

**Usage:** *ELECTRONIC\_TEMPERATURE \[K\] 300*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Electronic temperature used for Fermi-Dirac smearing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1324)\]

### EPS\_FERMI\_DIRAC*: real* *\= 1.00000000E-010*

**Usage:** *EPS\_FERMI\_DIRAC 1.0E-6*

Accuracy checks on occupation numbers use this as a tolerance \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1337)\]

### FIXED\_MAGNETIC\_MOMENT*: real* *\= \-1.00000000E+002*

**Usage:** *FIXED\_MAGNETIC\_MOMENT 1.5*

Imposed difference between the numbers of electrons of spin up and spin down: m = n(up) - n(down). A negative value (default) allows for a change of the magnetic moment. -1 specifically keeps an integer number of spin up and spin down electrons. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1373)\]

### LIST*: real\[ \]*

**Usage:** *LIST 2.0 0.6666 0.6666 0.66666 0.0 0.0*

A list of fractional occupations to use. Must match the number of states and sum up to the correct number of electrons \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1313)\]

### METHOD*: enum* *\= GAUSSIAN*

**Usage:** *METHOD Fermi\_Dirac*

**Valid values:**

-   `FERMI_DIRAC` Fermi-Dirac distribution defined by the keyword ELECTRONIC\_TEMPERATURE. Use this method if the temperature equivalence is important for you, e.g. if you want to compute some properties based on the occupations. If you use this method without interest in electronic temperature, it’s suggested to use extrapolated result from finite ELECTRONIC\_TEMPERATURE to ELECTRONIC\_TEMPERATURE = 0. Note the forces and stress are consistent with the free energy and not with the extrapolated energy.

-   `ENERGY_WINDOW` Energy window defined by the keyword WINDOW\_SIZE.

-   `LIST` Use a fixed list of occupations.

-   `GAUSSIAN` Gaussian broadening with width SIGMA; should work well in most cases. With this method you have to use extrapolated results from finite SIGMA results to SIGMA = 0, but usually this value would not be quite accurate without systematically reducing SIGMA. Note the forces and stress are consistent with the free energy and not with the extrapolated energy.

-   `METHFESSEL_PAXTON` First-order Methfessel-Paxton distribution with width SIGMA. Don’t use it for semiconductors and insulators because the partial occupancies can be unphysical and thus lead to wrong results.

-   `MARZARI_VANDERBILT` Marzari-Vanderbilt cold smearing with width SIGMA.


**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Selects the smearing method to apply. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1283)\]

### SIGMA*: real* *\= 2.00000000E-003 \[hartree\]*

**Usage:** *SIGMA \[eV\] 0.2*

**Mentions:** ⭐[How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)

Smearing width sigma (in energy units) in the case of Gaussian, Methfessel-Paxton or Marzari-Vanderbilt smearing. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1348)\]

### WINDOW\_SIZE*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *WINDOW\_SIZE \[eV\] 0.3*

Size of the energy window centred at the Fermi level \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_scf.F#L1361)\]
