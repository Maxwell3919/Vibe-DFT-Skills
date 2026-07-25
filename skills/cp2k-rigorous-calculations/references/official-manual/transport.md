# CP2K official manual snapshot: transport

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html
- Raw SHA-256: 96865ca920fb063a1a96358fdd7fd7a07d50f069326b23aa391b59ec216ff573
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# TRANSPORT

**References:** [Bruck2014](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#bruck2014)

Specifies the parameters for transport, sets parameters for the OMEN code, see also [https://nano-tcad.ee.ethz.ch](https://nano-tcad.ee.ethz.ch). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L61)\]

Subsections

-   [BEYN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT/BEYN.html)
-   [CONTACT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT/CONTACT.html)
-   [PEXSI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT/PEXSI.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT/PRINT.html)

## Keywords

-   [COLZERO\_THRESHOLD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.COLZERO_THRESHOLD "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.COLZERO_THRESHOLD")

-   [CONTACT\_FILLING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CONTACT_FILLING "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CONTACT_FILLING")

-   [CSR\_SCREENING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CSR_SCREENING "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CSR_SCREENING")

-   [CUTOUT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CUTOUT "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.CUTOUT")

-   [DENSITY\_MIXING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.DENSITY_MIXING "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.DENSITY_MIXING")

-   [ENERGY\_INTERVAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.ENERGY_INTERVAL "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.ENERGY_INTERVAL")

-   [EPS\_DECAY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_DECAY "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_DECAY")

-   [EPS\_EIGVAL\_DEGEN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_EIGVAL_DEGEN "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_EIGVAL_DEGEN")

-   [EPS\_FERMI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_FERMI "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_FERMI")

-   [EPS\_LIMIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_LIMIT "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_LIMIT")

-   [EPS\_LIMIT\_CC](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_LIMIT_CC "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_LIMIT_CC")

-   [EPS\_MU](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_MU "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_MU")

-   [EPS\_SINGULARITY\_CURVATURES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_SINGULARITY_CURVATURES "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.EPS_SINGULARITY_CURVATURES")

-   [GPUS\_PER\_POINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.GPUS_PER_POINT "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.GPUS_PER_POINT")

-   [INJECTION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.INJECTION_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.INJECTION_METHOD")

-   [LINEAR\_SOLVER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.LINEAR_SOLVER "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.LINEAR_SOLVER")

-   [MATRIX\_INVERSION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.MATRIX_INVERSION_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.MATRIX_INVERSION_METHOD")

-   [MIN\_INTERVAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.MIN_INTERVAL "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.MIN_INTERVAL")

-   [NUM\_INTERVAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.NUM_INTERVAL "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.NUM_INTERVAL")

-   [NUM\_POLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.NUM_POLE "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.NUM_POLE")

-   [N\_KPOINTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.N_KPOINTS "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.N_KPOINTS")

-   [N\_POINTS\_INV](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.N_POINTS_INV "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.N_POINTS_INV")

-   [OBC\_EQUILIBRIUM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.OBC_EQUILIBRIUM "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.OBC_EQUILIBRIUM")

-   [QT\_FORMALISM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.QT_FORMALISM "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.QT_FORMALISM")

-   [REAL\_AXIS\_INTEGRATION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.REAL_AXIS_INTEGRATION_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.REAL_AXIS_INTEGRATION_METHOD")

-   [TASKS\_PER\_ENERGY\_POINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TASKS_PER_ENERGY_POINT "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TASKS_PER_ENERGY_POINT")

-   [TASKS\_PER\_POLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TASKS_PER_POLE "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TASKS_PER_POLE")

-   [TEMPERATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TEMPERATURE "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TEMPERATURE")

-   [TRANSPORT\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html#CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TRANSPORT_METHOD "CP2K_INPUT.FORCE_EVAL.DFT.TRANSPORT.TRANSPORT_METHOD")


## Keyword descriptions

### COLZERO\_THRESHOLD*: real* *\= 1.00000000E-012*

**Usage:** *COLZERO\_THRESHOLD*

The smallest number that is not zero in the full diagonalization part. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L132)\]

### CONTACT\_FILLING*: enum* *\= BAND\_STRUCTURE*

**Valid values:**

-   `BAND_STRUCTURE` Determine the Fermi levels from the band structure.

-   `DOS` Determine the Fermi levels from the density of states.


Determination of the contact Fermi levels. Note that this keyword only works when the TRANSPORT\_METHOD is specified as TRANSPORT. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L272)\]

### CSR\_SCREENING*: logical* *\= T*

**Lone keyword:** `T`

Whether distance screening should be applied to improve sparsity of CSR matrices. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L201)\]

### CUTOUT*: integer\[2\]* *\= 0 0*

**Usage:** *CUTOUT*

The number of atoms at the beginning and the end of the structure where the density should not be changed. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L240)\]

### DENSITY\_MIXING*: real* *\= 1.00000000E+000*

**Usage:** *DENSITY\_MIXING*

Mixing parameter for a density mixing in OMEN. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L283)\]

### ENERGY\_INTERVAL*: real* *\= 1.00000000E-003*

**Usage:** *ENERGY\_INTERVAL*

Distance between energy points in eV. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L181)\]

### EPS\_DECAY*: real* *\= 1.00000000E-004*

**Usage:** *EPS\_DECAY*

The smallest imaginary part that a decaying eigenvalue may have not to be considered as propagating. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L150)\]

### EPS\_EIGVAL\_DEGEN*: real* *\= 1.00000000E-006*

**Usage:** *EPS\_EIGVAL\_DEGEN*

Filter for degenerate bands in the injection vector. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L169)\]

### EPS\_FERMI*: real* *\= 0.00000000E+000*

**Usage:** *EPS\_FERMI*

Cutoff for the tail of the Fermi function. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L175)\]

### EPS\_LIMIT*: real* *\= 1.00000000E-004*

**Usage:** *EPS\_LIMIT*

The smallest eigenvalue that is kept. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L138)\]

### EPS\_LIMIT\_CC*: real* *\= 1.00000000E-006*

**Usage:** *EPS\_LIMIT\_CC*

The smallest eigenvalue that is kept on the complex contour. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L144)\]

### EPS\_MU*: real* *\= 1.00000000E-006*

**Usage:** *EPS\_MU*

Accuracy to which the Fermi level should be determined. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L163)\]

### EPS\_SINGULARITY\_CURVATURES*: real* *\= 1.00000000E-012*

**Usage:** *EPS\_SINGULARITY\_CURVATURES*

Filter for degenerate bands in the bandstructure. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L157)\]

### GPUS\_PER\_POINT*: integer* *\= 2*

**Usage:** *GPUS\_PER\_POINT*

Number of GPUs per energy point for SplitSolve. Needs to be a power of two \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L126)\]

### INJECTION\_METHOD*: enum* *\= BEYN*

**Usage:** *INJECTION\_METHOD*

**Valid values:**

-   `EVP` Full eigenvalue solver.

-   `BEYN` Beyn eigenvalue solver.


Method to solve the eigenvalue problem for the open boundary conditions. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L228)\]

### LINEAR\_SOLVER*: enum* *\= FULL*

**Usage:** *LINEAR\_SOLVER*

**Valid values:**

-   `SPLITSOLVE`

-   `SUPERLU`

-   `MUMPS`

-   `FULL`

-   `BANDED`

-   `PARDISO`

-   `UMFPACK`


Preferred solver for solving the linear system of equations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L208)\]

### MATRIX\_INVERSION\_METHOD*: enum* *\= FULL*

**Usage:** *MATRIX\_INVERSION\_METHOD*

**Valid values:**

-   `FULL`

-   `PEXSI`

-   `PARDISO`

-   `RGF`


Preferred matrix inversion method. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L219)\]

### MIN\_INTERVAL*: real* *\= 1.00000000E-004*

**Usage:** *MIN\_INTERVAL*

Smallest enery distance in energy vector. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L187)\]

### NUM\_INTERVAL*: integer* *\= 10*

**Usage:** *NUM\_INTERVAL*

Max number of energy points per small interval. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L106)\]

### NUM\_POLE*: integer* *\= 64*

**Usage:** *NUM\_POLE*

The number of terms in the PEXSI’s pole expansion method. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L94)\]

### N\_KPOINTS*: integer* *\= 64*

**Usage:** *N\_KPOINTS*

The number of k points for determination of the singularities. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L100)\]

### N\_POINTS\_INV*: integer* *\= 64*

**Usage:** *N\_POINTS\_INV*

Number of integration points for the sigma solver on the complex contour. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L260)\]

### OBC\_EQUILIBRIUM*: logical* *\= F*

**Lone keyword:** `T`

Compute the equilibrium density with open boundary conditions. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L266)\]

### QT\_FORMALISM*: enum* *\= QTBM*

**Usage:** *QT\_FORMALISM*

**Valid values:**

-   `NEGF` The non-equilibrium Green’s function formalism.

-   `QTBM` The quantum transmitting boundary method / wave-function formalism.


Preferred quantum transport formalism to compute the current and density. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L83)\]

### REAL\_AXIS\_INTEGRATION\_METHOD*: enum* *\= GAUSS\_CHEBYSHEV*

**Usage:** *REAL\_AXIS\_INTEGRATION\_METHOD*

**Valid values:**

-   `GAUSS_CHEBYSHEV` Gauss-Chebyshev integration between singularity points.

-   `TRAPEZOIDAL_RULE` Trapezoidal rule on the total range.

-   `READ` Read integration points from a file (named E.dat).


Integration method for the real axis. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L248)\]

### TASKS\_PER\_ENERGY\_POINT*: integer* *\= 1*

**Usage:** *TASKS\_PER\_ENERGY\_POINT*

Number of tasks per energy point. The value should be a divisor of the total number of MPI ranks. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L112)\]

### TASKS\_PER\_POLE*: integer* *\= 1*

**Usage:** *TASKS\_PER\_POLE*

Number of tasks per pole in the pole expansion method. The value should be a divisor of the total number of MPI ranks. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L119)\]

### TEMPERATURE*: real* *\= 3.00000000E+002 \[K\]*

**Usage:** *TEMPERATURE \[K\] 300.0*

Temperature. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L193)\]

### TRANSPORT\_METHOD*: enum* *\= TRANSPORT*

**Usage:** *TRANSPORT\_METHOD*

**Valid values:**

-   `TRANSPORT` self-consistent CP2K and OMEN transport calculations

-   `LOCAL_SCF` CP2K valence Hamiltonian + OMEN self-consistent calculations on conduction electrons

-   `TRANSMISSION` self-consistent transmission calculations without applied bias voltage


Preferred method for transport calculations. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_transport.F#L70)\]
