# CP2K official manual snapshot: ext-restart

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/EXT_RESTART.html
- Raw SHA-256: 791a924502301466166227e3c90cb33e497727d6e6dbfbd873e544a7676301d2
- Status: version-matched cached official text; reopen the source for current live verification.

EXT_RESTART



Section for external restart, specifies an external input file where to take positions, etc. By default they are all set to TRUE

[

Edit on GitHub

]

Keywords



BINARY_RESTART_FILE_NAME

CUSTOM_PATH

RESTART_AVERAGES

RESTART_BAND

RESTART_BAROSTAT

RESTART_BAROSTAT_THERMOSTAT

RESTART_BSSE

RESTART_CELL

RESTART_CONSTRAINT

RESTART_CORE_POS

RESTART_CORE_VELOCITY

RESTART_COUNTERS

RESTART_DEFAULT

RESTART_DIMER

RESTART_FILE_NAME

RESTART_HELIUM_AVERAGES

RESTART_HELIUM_DENSITIES

RESTART_HELIUM_FORCE

RESTART_HELIUM_PERMUTATION

RESTART_HELIUM_POS

RESTART_HELIUM_RNG

RESTART_METADYNAMICS

RESTART_OPTIMIZE_INPUT_VARIABLES

RESTART_PINT_GLE

RESTART_PINT_NOSE

RESTART_PINT_POS

RESTART_PINT_VEL

RESTART_POS

RESTART_QMMM

RESTART_RANDOMG

RESTART_RTP

RESTART_SHELL_POS

RESTART_SHELL_THERMOSTAT

RESTART_SHELL_VELOCITY

RESTART_TEMPERATURE_ANNEALING

RESTART_THERMOSTAT

RESTART_VEL

RESTART_WALKERS

Keyword descriptions



BINARY_RESTART_FILE_NAME

:

string



Aliases:

BINARY_RESTART_FILE

Specifies the name of an additional restart file from which selected input sections are read in binary format (see SPLIT_RESTART_FILE).

[

Edit on GitHub

]

CUSTOM_PATH

:

string



Keyword can be repeated.

Restarts the given path from the EXTERNAL file. Allows a major flexibility for restarts.

[

Edit on GitHub

]

RESTART_AVERAGES

:

logical



Lone keyword:

T

Restarts information for AVERAGES.

[

Edit on GitHub

]

RESTART_BAND

:

logical



Lone keyword:

T

Restarts positions and velocities of the Band.

[

Edit on GitHub

]

RESTART_BAROSTAT

:

logical



Lone keyword:

T

Restarts the barostat from the external file

[

Edit on GitHub

]

RESTART_BAROSTAT_THERMOSTAT

:

logical



Lone keyword:

T

Restarts the barostat thermostat from the external file

[

Edit on GitHub

]

RESTART_BSSE

:

logical



Lone keyword:

T

Restarts information for BSSE calculations.

[

Edit on GitHub

]

RESTART_CELL

:

logical



Lone keyword:

T

Restarts the cell (and cell_ref) from the EXTERNAL file

[

Edit on GitHub

]

RESTART_CONSTRAINT

:

logical



Lone keyword:

T

Restarts constraint section. It’s necessary when doing restraint calculation to have a perfect energy conservation. For constraints only its use is optional.

[

Edit on GitHub

]

RESTART_CORE_POS

:

logical



Lone keyword:

T

Takes the positions of the cores from the external file (only if shell-model)

[

Edit on GitHub

]

RESTART_CORE_VELOCITY

:

logical



Lone keyword:

T

Takes the velocities of the shells from the external file (only if shell-model)

[

Edit on GitHub

]

RESTART_COUNTERS

:

logical



Lone keyword:

T

Restarts the counters in MD schemes and optimization STEP

[

Edit on GitHub

]

RESTART_DEFAULT

:

logical

=

T



This keyword controls the default value for all possible restartable keywords, unless explicitly defined. For example setting this keyword to .FALSE. does not restart any quantity. If, at the same time, one keyword is set to .TRUE. only that quantity will be restarted.

[

Edit on GitHub

]

RESTART_DIMER

:

logical



Lone keyword:

T

Restarts information for DIMER geometry optimizations.

[

Edit on GitHub

]

RESTART_FILE_NAME

:

string



Aliases:

EXTERNAL_FILE

Specifies the name of restart file (or any other input file) to be read. Only fields relevant to a restart will be used (unless switched off with the keywords in this section)

[

Edit on GitHub

]

RESTART_HELIUM_AVERAGES

:

logical

=

F



Lone keyword:

T

Restarts average properties from PINT%HELIUM%AVERAGES.

[

Edit on GitHub

]

RESTART_HELIUM_DENSITIES

:

logical

=

F



Lone keyword:

T

Restarts helium density distributions from PINT%HELIUM%RHO.

[

Edit on GitHub

]

RESTART_HELIUM_FORCE

:

logical



Lone keyword:

T

Restart helium forces exerted on the solute from PINT%HELIUM%FORCE.

[

Edit on GitHub

]

RESTART_HELIUM_PERMUTATION

:

logical



Lone keyword:

T

Restart helium permutation state from PINT%HELIUM%PERM.

[

Edit on GitHub

]

RESTART_HELIUM_POS

:

logical



Lone keyword:

T

Restart helium positions from PINT%HELIUM%COORD.

[

Edit on GitHub

]

RESTART_HELIUM_RNG

:

logical



Lone keyword:

T

Restarts helium random number generators from PINT%HELIUM%RNG_STATE.

[

Edit on GitHub

]

RESTART_METADYNAMICS

:

logical



Lone keyword:

T

Restarts hills from a previous metadynamics run from the EXTERNAL file

[

Edit on GitHub

]

RESTART_OPTIMIZE_INPUT_VARIABLES

:

logical



Lone keyword:

T

Restart with the optimize input variables

[

Edit on GitHub

]

RESTART_PINT_GLE

:

logical



Lone keyword:

T

Restart GLE thermostat for beads from PINT%GLE.

[

Edit on GitHub

]

RESTART_PINT_NOSE

:

logical



Lone keyword:

T

Restart Nose thermostat for beads from PINT%NOSE.

[

Edit on GitHub

]

RESTART_PINT_POS

:

logical



Lone keyword:

T

Restart bead positions from PINT%BEADS%COORD.

[

Edit on GitHub

]

RESTART_PINT_VEL

:

logical



Lone keyword:

T

Restart bead velocities from PINT%BEADS%VELOCITY.

[

Edit on GitHub

]

RESTART_POS

:

logical



Lone keyword:

T

Takes the positions from the external file

[

Edit on GitHub

]

RESTART_QMMM

:

logical



Lone keyword:

T

Restarts the following specific QMMM info: translation vectors.

[

Edit on GitHub

]

RESTART_RANDOMG

:

logical



Lone keyword:

T

Restarts the random number generator from the external file

[

Edit on GitHub

]

RESTART_RTP

:

logical



Lone keyword:

T

Restarts information for REAL TIME PROPAGATION and EHRENFEST DYNAMICS.

[

Edit on GitHub

]

RESTART_SHELL_POS

:

logical



Lone keyword:

T

Takes the positions of the shells from the external file (only if shell-model)

[

Edit on GitHub

]

RESTART_SHELL_THERMOSTAT

:

logical



Lone keyword:

T

Restarts the shell thermostat from the external file

[

Edit on GitHub

]

RESTART_SHELL_VELOCITY

:

logical



Lone keyword:

T

Takes the velocities of the shells from the external file (only if shell-model)

[

Edit on GitHub

]

RESTART_TEMPERATURE_ANNEALING

:

logical

=

F



Lone keyword:

T

Restarts external temperature when using TEMPERATURE_ANNEALING.

[

Edit on GitHub

]

RESTART_THERMOSTAT

:

logical



Lone keyword:

T

Restarts the nose thermostats of the particles from the EXTERNAL file

[

Edit on GitHub

]

RESTART_VEL

:

logical



Lone keyword:

T

Takes the velocities from the external file

[

Edit on GitHub

]

RESTART_WALKERS

:

logical



Lone keyword:

T

Restarts walkers informations from a previous metadynamics run from the EXTERNAL file

[

Edit on GitHub

]
