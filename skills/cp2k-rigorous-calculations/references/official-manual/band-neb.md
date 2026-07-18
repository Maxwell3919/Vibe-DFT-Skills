# CP2K official manual snapshot: band-neb

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html
- Raw SHA-256: 1efc9c5f25da266f97cd04fc08c8ac454c89d45bea66b7a2d4d34c0ee4e97657
- Status: version-matched cached official text; reopen the source for current live verification.

BAND



References:

Elber1987

,

Jonsson1998

,

Henkelman2000b

,

Henkelman2000

,

Trygubenko2004

The section that controls a BAND run

[

Edit on GitHub

]

Subsections

BANNER

CI_NEB

CONVERGENCE_CONTROL

CONVERGENCE_INFO

ENERGY

FINAL_BAND

OPTIMIZE_BAND

PROGRAM_RUN_INFO

REPLICA

REPLICA_INFO

STRING_METHOD

Keywords



ALIGN_FRAMES

BAND_TYPE

K_SPRING

NPROC_REP

NUMBER_OF_REPLICA

POT_TYPE

PROC_DIST_TYPE

ROTATE_FRAMES

USE_COLVARS

Keyword descriptions



ALIGN_FRAMES

:

logical

=

T



Lone keyword:

T

Enables the alignment of the frames at the beginning of a BAND calculation. This keyword does not affect the rotation of the replicas during a BAND calculation.

[

Edit on GitHub

]

BAND_TYPE

:

enum

=

IT-NEB



Usage:

BAND_TYPE (B-NEB|IT-NEB|CI-NEB|D-NEB|SM|EB)

Valid values:

B-NEB

Bisection nudged elastic band

IT-NEB

Improved tangent nudged elastic band

CI-NEB

Climbing image nudged elastic band

D-NEB

Doubly nudged elastic band

SM

String Method

EB

Elastic band (Hamiltonian formulation)

Specifies the type of BAND calculation

[

Edit on GitHub

]

K_SPRING

:

real

=

2.00000000E-002



Aliases:

K

Specify the value of the spring constant

[

Edit on GitHub

]

NPROC_REP

:

integer

=

1



Specify the number of processors to be used per replica environment (for parallel runs)

[

Edit on GitHub

]

NUMBER_OF_REPLICA

:

integer

=

10



Specify the number of Replica to use in the BAND. This may be equal to or larger than the number of defined &REPLICA sections. If larger, the rest of missing replica will automatically be interpolated in an iterative bisection procedure: on each step, the largest distance between adjacent replica is found and a new replica is inserted there by taking the average of adjacent replica; this is repeated until getting requested number of replica. Please note that the number of replica is always including both end points regardless of the setting of keyword OPTIMIZE_END_POINTS, which should be taken into account when adjusting the NPROC_REP value based on processors available on the machine.

[

Edit on GitHub

]

POT_TYPE

:

enum

=

FULL



Usage:

POT_TYPE (FULL|FE|ME)

Valid values:

FULL

Full potential (no projections in a subspace of colvars)

FE

Free energy (requires a projections in a subspace of colvars)

ME

Minimum energy (requires a projections in a subspace of colvars)

Specifies the type of potential used in the BAND calculation

[

Edit on GitHub

]

PROC_DIST_TYPE

:

enum

=

BLOCKED



Usage:

PROC_DIST_TYPE (INTERLEAVED|BLOCKED)

Valid values:

INTERLEAVED

Interleaved distribution

BLOCKED

Blocked distribution

Specify the topology of the mapping of processors into replicas.

[

Edit on GitHub

]

ROTATE_FRAMES

:

logical

=

T



Lone keyword:

T

Compute at each BAND step the RMSD and rotate the frames in order to minimize it.

[

Edit on GitHub

]

USE_COLVARS

:

logical

=

F



Lone keyword:

T

Uses a version of the band scheme projected in a subspace of colvars.

[

Edit on GitHub

]
