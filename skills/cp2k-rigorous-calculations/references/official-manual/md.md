# CP2K official manual snapshot: md

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD.html
- Raw SHA-256: 8011288b61146f408ba50c18b1923c3717bd15a64300e760e9baf0c9dc2ff2c2
- Status: version-matched cached official text; reopen the source for current live verification.

MD



This section defines the whole set of parameters needed perform an MD run.

[

Edit on GitHub

]

Subsections

ADIABATIC_DYNAMICS

AVERAGES

BAROSTAT

CASCADE

INITIAL_VIBRATION

LANGEVIN

MSST

PRINT

REFTRAJ

RESPA

SHELL

THERMAL_REGION

THERMOSTAT

VELOCITY_SOFTENING

Keywords



ANGVEL_TOL

ANGVEL_ZERO

ANNEALING

ANNEALING_CELL

COMVEL_TOL

DISPLACEMENT_TOL

ECONS_START_VAL

ENSEMBLE

INITIALIZATION_METHOD

MAX_STEPS

SCALE_TEMP_KIND

STEPS

STEP_START_VAL

TEMPERATURE

TEMPERATURE_ANNEALING

TEMP_KIND

TEMP_TOL

TIMESTEP

TIME_START_VAL

Keyword descriptions



ANGVEL_TOL

:

real

=

[au_t^-1*bohr]



Usage:

ANGVEL_TOL 0.1

The maximum accepted angular velocity. This option is ignored when the system is periodic. Removes the components of the velocities that project on the external rotational degrees of freedom.

[

Edit on GitHub

]

ANGVEL_ZERO

:

logical

=

F



Lone keyword:

T

Usage:

ANGVEL_ZERO LOGICAL

Set the initial angular velocity to zero. This option is ignored when the system is periodic or when initial velocities are defined. Technically, the part of the random initial velocities that projects on the external rotational degrees of freedom is subtracted.

[

Edit on GitHub

]

ANNEALING

:

real

=

1.00000000E+000



Usage:

annealing

Specifies the rescaling factor for annealing velocities. Automatically enables the annealing procedure. This scheme works only for ensembles that do not have thermostats on particles.

[

Edit on GitHub

]

ANNEALING_CELL

:

real

=

1.00000000E+000



Usage:

ANNEALING_CELL

Specifies the rescaling factor for annealing velocities of the CELL Automatically enables the annealing procedure for the CELL. This scheme works only for ensambles that do not have thermostat on CELLS velocities.

[

Edit on GitHub

]

COMVEL_TOL

:

real

=

[au_t^-1*bohr]



Usage:

COMVEL_TOL 0.1

Mentions:

⭐

Molecular Dynamics

The maximum accepted velocity of the center of mass. With Shell-Model, comvel may drift if MD%THERMOSTAT%REGION /= GLOBAL

[

Edit on GitHub

]

DISPLACEMENT_TOL

:

real

=

5.29177209E+001

[angstrom]



Usage:

DISPLACEMENT_TOL

This keyword sets a maximum atomic displacement in each Cartesian direction. The maximum velocity is evaluated and if it is too large to remain within the assigned limit, the time step is rescaled accordingly, and the first half step of the velocity verlet is repeated.

[

Edit on GitHub

]

ECONS_START_VAL

:

real

=

0.00000000E+000

[hartree]



Usage:

ECONS_START_VAL

The starting value of the conserved quantity

[

Edit on GitHub

]

ENSEMBLE

:

enum

=

NVE



Usage:

ensemble nve

Valid values:

NVE

constant energy (microcanonical)

NVT

constant temperature and volume (canonical)

NPT_I

constant temperature and pressure using an isotropic cell

NPT_F

constant temperature and pressure using a flexible cell

MSST

simulate steady shock (uniaxial)

MSST_DAMPED

simulate steady shock (uniaxial) with extra viscosity

HYDROSTATICSHOCK

simulate steady shock with hydrostatic pressure

ISOKIN

constant kinetic energy

REFTRAJ

reading frames from a file called reftraj.xyz (e.g. for property calculation)

LANGEVIN

langevin dynamics (constant temperature)

NPE_F

constant pressure ensemble (no thermostat)

NPE_I

constant pressure ensemble using an isotropic cell (no thermostat)

NVT_ADIABATIC

adiabatic dynamics in constant temperature and volume ensemble (CAFES)

NPT_IA

NPT_I ensemble with frozen atoms in absolute coordinate

References:

Evans1983

,

VandeVondele2002

,

Minary2003

Mentions:

⭐

QM/MM with Built-in Force Field

, ⭐

Langevin Dynamics

, ⭐

Molecular Dynamics

The ensemble/integrator that you want to use for MD propagation

[

Edit on GitHub

]

INITIALIZATION_METHOD

:

enum

=

DEFAULT



Usage:

INITIALIZATION_METHOD DEFAULT

Valid values:

DEFAULT

Assign random velocities and then scale according to TEMPERATURE

VIBRATIONAL

Initialise positions and velocities to give canonical ensemble with TEMPERATURE, using the method described in PRL 96, 115504 (2006)

Mentions:

⭐

Molecular Dynamics

This keyword selects which method to use to initialize MD. If velecities are not set explicitly, DEFAULT optioin will assign random velocities and then scale according to TEMPERATURE; VIBRATIONAL option will then use previously calculated vibrational modes to initialise both the atomic positions and velocities so that the starting point for MD is as close to canonical ensemble as possible, without the need for lengthy equilibration steps. See PRL 96, 115504 (2006). The user input atomic positions in this case are expected to be already geometry optimised. Further options for VIBRATIONAL mode is can be set in INITIAL_VIBRATION subsection. If unspecified, then the DEFAULT mode will be used.

[

Edit on GitHub

]

MAX_STEPS

:

integer

=

1000000000



Usage:

MAX_STEPS 100

The number of MD steps to perform, counting from step 1

[

Edit on GitHub

]

SCALE_TEMP_KIND

:

logical

=

F



Lone keyword:

T

Usage:

SCALE_TEMP_KIND LOGICAL

When necessary rescale the temperature per each kind separately

[

Edit on GitHub

]

STEPS

:

integer

=

3



Usage:

STEPS 100

Mentions:

⭐

Real-Time Propagation and Ehrenfest MD

The number of MD steps to perform, counting from step_start_val.

[

Edit on GitHub

]

STEP_START_VAL

:

integer

=

0



Usage:

STEP_START_VAL

The starting step value for the MD

[

Edit on GitHub

]

TEMPERATURE

:

real

=

3.00000000E+002

[K]



Usage:

TEMPERATURE 325.0

Mentions:

⭐

Langevin Dynamics

, ⭐

Molecular Dynamics

The temperature in K used to initialize the velocities with init and pos restart, and in the NPT/NVT simulations

[

Edit on GitHub

]

TEMPERATURE_ANNEALING

:

real

=

1.00000000E+000



Usage:

TEMPERATURE_ANNEALING

Specifies the rescaling factor for the external temperature. This scheme works only for the Langevin ensemble.

[

Edit on GitHub

]

TEMP_KIND

:

logical

=

F



Lone keyword:

T

Usage:

TEMP_KIND LOGICAL

Compute the temperature per each kind separately

[

Edit on GitHub

]

TEMP_TOL

:

real

=

0.00000000E+000

[K]



Aliases:

TEMP_TO ,TEMPERATURE_TOLERANCE

Usage:

TEMP_TOL 0.0

Mentions:

⭐

Molecular Dynamics

The maximum accepted deviation of the (global) temperature from the desired target temperature before a rescaling of the velocities is performed. If it is 0 no rescaling is performed. NOTE: This keyword is obsolescent; Using a CSVR thermostat with a short timeconstant is recommended as a better alternative.

[

Edit on GitHub

]

TIMESTEP

:

real

=

5.00000000E-001

[fs]



Usage:

TIMESTEP 1.0

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

X-Ray Absorption from RTP and \delta-Kick perturbation

, ⭐

QM/MM with Built-in Force Field

, ⭐

Real-Time Propagation and Ehrenfest MD

, ⭐

Molecular Dynamics

The length of an integration step (in case RESPA the large TIMESTEP)

[

Edit on GitHub

]

TIME_START_VAL

:

real

=

0.00000000E+000

[fs]



Usage:

TIME_START_VAL

The starting timer value for the MD

[

Edit on GitHub

]
