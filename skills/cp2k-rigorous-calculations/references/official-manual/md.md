# CP2K official manual snapshot: md

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html
- Raw SHA-256: 8011288b61146f408ba50c18b1923c3717bd15a64300e760e9baf0c9dc2ff2c2
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# MD

This section defines the whole set of parameters needed perform an MD run. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L81)\]

Subsections

-   [ADIABATIC\_DYNAMICS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/ADIABATIC_DYNAMICS.html)
-   [AVERAGES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/AVERAGES.html)
-   [BAROSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html)
-   [CASCADE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/CASCADE.html)
-   [INITIAL\_VIBRATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/INITIAL_VIBRATION.html)
-   [LANGEVIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/LANGEVIN.html)
-   [MSST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/MSST.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/PRINT.html)
-   [REFTRAJ](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/REFTRAJ.html)
-   [RESPA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/RESPA.html)
-   [SHELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/SHELL.html)
-   [THERMAL\_REGION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMAL_REGION.html)
-   [THERMOSTAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT.html)
-   [VELOCITY\_SOFTENING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/VELOCITY_SOFTENING.html)

## Keywords

-   [ANGVEL\_TOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ANGVEL_TOL "CP2K_INPUT.MOTION.MD.ANGVEL_TOL")

-   [ANGVEL\_ZERO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ANGVEL_ZERO "CP2K_INPUT.MOTION.MD.ANGVEL_ZERO")

-   [ANNEALING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ANNEALING "CP2K_INPUT.MOTION.MD.ANNEALING")

-   [ANNEALING\_CELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ANNEALING_CELL "CP2K_INPUT.MOTION.MD.ANNEALING_CELL")

-   **[COMVEL\_TOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.COMVEL_TOL "CP2K_INPUT.MOTION.MD.COMVEL_TOL")**

-   [DISPLACEMENT\_TOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.DISPLACEMENT_TOL "CP2K_INPUT.MOTION.MD.DISPLACEMENT_TOL")

-   [ECONS\_START\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ECONS_START_VAL "CP2K_INPUT.MOTION.MD.ECONS_START_VAL")

-   **[ENSEMBLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.ENSEMBLE "CP2K_INPUT.MOTION.MD.ENSEMBLE")**

-   **[INITIALIZATION\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.INITIALIZATION_METHOD "CP2K_INPUT.MOTION.MD.INITIALIZATION_METHOD")**

-   [MAX\_STEPS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.MAX_STEPS "CP2K_INPUT.MOTION.MD.MAX_STEPS")

-   [SCALE\_TEMP\_KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.SCALE_TEMP_KIND "CP2K_INPUT.MOTION.MD.SCALE_TEMP_KIND")

-   **[STEPS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.STEPS "CP2K_INPUT.MOTION.MD.STEPS")**

-   [STEP\_START\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.STEP_START_VAL "CP2K_INPUT.MOTION.MD.STEP_START_VAL")

-   **[TEMPERATURE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TEMPERATURE "CP2K_INPUT.MOTION.MD.TEMPERATURE")**

-   [TEMPERATURE\_ANNEALING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TEMPERATURE_ANNEALING "CP2K_INPUT.MOTION.MD.TEMPERATURE_ANNEALING")

-   [TEMP\_KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TEMP_KIND "CP2K_INPUT.MOTION.MD.TEMP_KIND")

-   **[TEMP\_TOL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TEMP_TOL "CP2K_INPUT.MOTION.MD.TEMP_TOL")**

-   **[TIMESTEP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TIMESTEP "CP2K_INPUT.MOTION.MD.TIMESTEP")**

-   [TIME\_START\_VAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html#CP2K_INPUT.MOTION.MD.TIME_START_VAL "CP2K_INPUT.MOTION.MD.TIME_START_VAL")


## Keyword descriptions

### ANGVEL\_TOL*: real* *\= \[au\_t^-1\*bohr\]*

**Usage:** *ANGVEL\_TOL 0.1*

The maximum accepted angular velocity. This option is ignored when the system is periodic. Removes the components of the velocities that project on the external rotational degrees of freedom. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L194)\]

### ANGVEL\_ZERO*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ANGVEL\_ZERO LOGICAL*

Set the initial angular velocity to zero. This option is ignored when the system is periodic or when initial velocities are defined. Technically, the part of the random initial velocities that projects on the external rotational degrees of freedom is subtracted. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L202)\]

### ANNEALING*: real* *\= 1.00000000E+000*

**Usage:** *annealing*

Specifies the rescaling factor for annealing velocities. Automatically enables the annealing procedure. This scheme works only for ensembles that do not have thermostats on particles. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L212)\]

### ANNEALING\_CELL*: real* *\= 1.00000000E+000*

**Usage:** *ANNEALING\_CELL*

Specifies the rescaling factor for annealing velocities of the CELL Automatically enables the annealing procedure for the CELL. This scheme works only for ensambles that do not have thermostat on CELLS velocities. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L220)\]

### COMVEL\_TOL*: real* *\= \[au\_t^-1\*bohr\]*

**Usage:** *COMVEL\_TOL 0.1*

**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

The maximum accepted velocity of the center of mass. With Shell-Model, comvel may drift if MD%THERMOSTAT%REGION /= GLOBAL \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L187)\]

### DISPLACEMENT\_TOL*: real* *\= 5.29177209E+001 \[angstrom\]*

**Usage:** *DISPLACEMENT\_TOL*

This keyword sets a maximum atomic displacement in each Cartesian direction. The maximum velocity is evaluated and if it is too large to remain within the assigned limit, the time step is rescaled accordingly, and the first half step of the velocity verlet is repeated. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L235)\]

### ECONS\_START\_VAL*: real* *\= 0.00000000E+000 \[hartree\]*

**Usage:** *ECONS\_START\_VAL*

The starting value of the conserved quantity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L147)\]

### ENSEMBLE*: enum* *\= NVE*

**Usage:** *ensemble nve*

**Valid values:**

-   `NVE` constant energy (microcanonical)

-   `NVT` constant temperature and volume (canonical)

-   `NPT_I` constant temperature and pressure using an isotropic cell

-   `NPT_F` constant temperature and pressure using a flexible cell

-   `MSST` simulate steady shock (uniaxial)

-   `MSST_DAMPED` simulate steady shock (uniaxial) with extra viscosity

-   `HYDROSTATICSHOCK` simulate steady shock with hydrostatic pressure

-   `ISOKIN` constant kinetic energy

-   `REFTRAJ` reading frames from a file called reftraj.xyz (e.g. for property calculation)

-   `LANGEVIN` langevin dynamics (constant temperature)

-   `NPE_F` constant pressure ensemble (no thermostat)

-   `NPE_I` constant pressure ensemble using an isotropic cell (no thermostat)

-   `NVT_ADIABATIC` adiabatic dynamics in constant temperature and volume ensemble (CAFES)

-   `NPT_IA` NPT\_I ensemble with frozen atoms in absolute coordinate


**References:** [Evans1983](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#evans1983), [VandeVondele2002](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2002), [Minary2003](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#minary2003)

**Mentions:** ⭐[QM/MM with Built-in Force Field](https://manual.cp2k.org/cp2k-2026_2-branch/methods/qm_mm/builtin.html), ⭐[Langevin Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/langevin_dynamics.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

The ensemble/integrator that you want to use for MD propagation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L86)\]

### INITIALIZATION\_METHOD*: enum* *\= DEFAULT*

**Usage:** *INITIALIZATION\_METHOD DEFAULT*

**Valid values:**

-   `DEFAULT` Assign random velocities and then scale according to TEMPERATURE

-   `VIBRATIONAL` Initialise positions and velocities to give canonical ensemble with TEMPERATURE, using the method described in PRL 96, 115504 (2006)


**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

This keyword selects which method to use to initialize MD. If velecities are not set explicitly, DEFAULT optioin will assign random velocities and then scale according to TEMPERATURE; VIBRATIONAL option will then use previously calculated vibrational modes to initialise both the atomic positions and velocities so that the starting point for MD is as close to canonical ensemble as possible, without the need for lengthy equilibration steps. See PRL 96, 115504 (2006). The user input atomic positions in this case are expected to be already geometry optimised. Further options for VIBRATIONAL mode is can be set in INITIAL\_VIBRATION subsection. If unspecified, then the DEFAULT mode will be used. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L246)\]

### MAX\_STEPS*: integer* *\= 1000000000*

**Usage:** *MAX\_STEPS 100*

The number of MD steps to perform, counting from step 1 \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L121)\]

### SCALE\_TEMP\_KIND*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SCALE\_TEMP\_KIND LOGICAL*

When necessary rescale the temperature per each kind separately \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L180)\]

### STEPS*: integer* *\= 3*

**Usage:** *STEPS 100*

**Mentions:** ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html)

The number of MD steps to perform, counting from step\_start\_val. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L115)\]

### STEP\_START\_VAL*: integer* *\= 0*

**Usage:** *STEP\_START\_VAL*

The starting step value for the MD \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L134)\]

### TEMPERATURE*: real* *\= 3.00000000E+002 \[K\]*

**Usage:** *TEMPERATURE 325.0*

**Mentions:** ⭐[Langevin Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/langevin_dynamics.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

The temperature in K used to initialize the velocities with init and pos restart, and in the NPT/NVT simulations \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L154)\]

### TEMPERATURE\_ANNEALING*: real* *\= 1.00000000E+000*

**Usage:** *TEMPERATURE\_ANNEALING*

Specifies the rescaling factor for the external temperature. This scheme works only for the Langevin ensemble. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L228)\]

### TEMP\_KIND*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *TEMP\_KIND LOGICAL*

Compute the temperature per each kind separately \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L173)\]

### TEMP\_TOL*: real* *\= 0.00000000E+000 \[K\]*

**Aliases:** TEMP\_TO ,TEMPERATURE\_TOLERANCE

**Usage:** *TEMP\_TOL 0.0*

**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

The maximum accepted deviation of the (global) temperature from the desired target temperature before a rescaling of the velocities is performed. If it is 0 no rescaling is performed. NOTE: This keyword is obsolescent; Using a CSVR thermostat with a short timeconstant is recommended as a better alternative. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L162)\]

### TIMESTEP*: real* *\= 5.00000000E-001 \[fs\]*

**Usage:** *TIMESTEP 1.0*

**Mentions:** ⭐[Real-Time Bethe-Salpeter Propagation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/rtbse.html), ⭐[X-Ray Absorption from RTP and \\delta-Kick perturbation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/delta-kick.html), ⭐[QM/MM with Built-in Force Field](https://manual.cp2k.org/cp2k-2026_2-branch/methods/qm_mm/builtin.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

The length of an integration step (in case RESPA the large TIMESTEP) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L127)\]

### TIME\_START\_VAL*: real* *\= 0.00000000E+000 \[fs\]*

**Usage:** *TIME\_START\_VAL*

The starting timer value for the MD \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/motion/input_cp2k_md.F#L140)\]
