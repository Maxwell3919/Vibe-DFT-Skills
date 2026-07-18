# CP2K official manual snapshot: kpoints

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html
- Raw SHA-256: d51fff85ac2d146cdc4d656682781a955e661b7e9278085dba2d207409091be2
- Status: version-matched cached official text; reopen the source for current live verification.

KPOINTS



Controls Brillouin-zone sampling with k-points.

[

Edit on GitHub

]

Keywords



DEBUG_FULL_KPOINT_SYMMETRY

EPS_SYMMETRY

FULL_GRID

GAMMA_CENTERED

INVERSION_SYMMETRY_ONLY

KPOINT

PARALLEL_GROUP_SIZE

SCHEME

SYMMETRY

SYMMETRY_BACKEND

SYMMETRY_REDUCTION_METHOD

UNITS

VERBOSE

WAVEFUNCTIONS

Keyword descriptions



DEBUG_FULL_KPOINT_SYMMETRY

:

logical

=

T



Lone keyword:

T

Usage:

DEBUG_FULL_KPOINT_SYMMETRY

Mentions:

⭐

K-Points

Use full atomic k-point symmetry also for DEBUG finite-difference points. This is enabled by default so analytical and finite-difference evaluations use the symmetry of their current geometry. Disable it to restrict DEBUG finite-difference energies to inversion/time-reversal symmetry.

[

Edit on GitHub

]

EPS_SYMMETRY

:

real

=

1.00000000E-006



Aliases:

EPS_GEO

Usage:

EPS_SYMMETRY

Mentions:

⭐

K-Points

Accuracy in k-point symmetry determination.

EPS_GEO is accepted as an alias.

[

Edit on GitHub

]

FULL_GRID

:

logical

=

F



Lone keyword:

T

Usage:

FULL_GRID

Use the full, non-symmetry-reduced k-point grid.

[

Edit on GitHub

]

GAMMA_CENTERED

:

logical

=

F



Lone keyword:

T

Usage:

GAMMA_CENTERED

Mentions:

⭐

K-Points

Generate a gamma-centered variant of the Monkhorst-Pack or MacDonald mesh. This shifts the original mesh so it can include the Gamma point, and makes sense only when an even number of subdivisions is used. For MacDonald meshes, the explicit shift is applied after the gamma-centering shift.

[

Edit on GitHub

]

INVERSION_SYMMETRY_ONLY

:

logical

=

F



Lone keyword:

T

Usage:

INVERSION_SYMMETRY_ONLY

Mentions:

⭐

K-Points

Restrict k-point reduction to k-space inversion (time-reversal) symmetry.

[

Edit on GitHub

]

KPOINT

:

real

[

4

]



Keyword can be repeated.

Usage:

KPOINT x y z w

Mentions:

⭐

K-Points

Specify kpoint coordinates and weight.

[

Edit on GitHub

]

PARALLEL_GROUP_SIZE

:

integer

=

-1



Usage:

PARALLEL_GROUP_SIZE

Mentions:

⭐

K-Points

Number of MPI processes to be used for a single k-point. This number must divide the total number of processes. The number of groups must divide the total number of kpoints. Value=-1 (smallest possible number of processes per group, satisfying the constraints). Value=0 (all processes). Value=n (exactly n processes).

[

Edit on GitHub

]

SCHEME

:

string[

]



Usage:

SCHEME {KPMETHOD} {integer} {integer} ..

References:

Monkhorst1976

,

MacDonald1978

Mentions:

⭐

K-Points

K-point generation scheme. Available options are:

NONE

GAMMA

MONKHORST-PACK

MACDONALD

GENERAL

For

MONKHORST-PACK

the number of k points in all 3 dimensions has to be supplied along with the keyword. For

MACDONALD

also the list of shifts. E.g.

MONKHORST-PACK

12

8

,

MACDONALD

4

0.25

.

GENERAL

uses explicitly listed k-points. If symmetry reduction is requested, the explicit set must be equally weighted and closed under the selected operations.

[

Edit on GitHub

]

SYMMETRY

:

logical

=

F



Lone keyword:

T

Usage:

SYMMETRY

Mentions:

⭐

K-Points

Use symmetry to reduce the number of kpoints.

[

Edit on GitHub

]

SYMMETRY_BACKEND

:

enum

=

K290



Usage:

SYMMETRY_BACKEND K290

Valid values:

K290

Use the existing K290 k-point symmetry backend.

SPGLIB

Use SPGLIB symmetry operations as k-point symmetry backend.

Mentions:

⭐

K-Points

Select the backend used to provide and apply atomic k-point symmetry operations. K290 is the established default. SPGLIB uses the symmetry operations returned by SPGLIB, including their fractional translations. This applies to Monkhorst-Pack, MacDonald, and closed GENERAL k-point sets. If SYMMETRY_REDUCTION_METHOD is not specified, it follows the selected backend.

[

Edit on GitHub

]

SYMMETRY_REDUCTION_METHOD

:

enum

=

K290



Usage:

SYMMETRY_REDUCTION_METHOD K290

Valid values:

K290

Use the existing K290 k-point symmetry reduction method.

SPGLIB

Use SPGLIB symmetry operations for k-point reduction.

Mentions:

⭐

K-Points

Select the method used to reduce Monkhorst-Pack and MacDonald k-point meshes when atomic symmetry is enabled. K290 is the established default. SPGLIB uses the symmetry operations returned by SPGLIB for the k-point reduction. GENERAL k-point lists can be reduced when the explicit set is equally weighted and closed under the selected operations. With SYMMETRY_BACKEND K290 this can be used as a comparison mode using K290 operations for SPGLIB-generated mappings.

[

Edit on GitHub

]

UNITS

:

string

=

B_VECTOR



Usage:

UNITS

Mentions:

⭐

K-Points

Special k-points are defined either in units of reciprocal lattice vectors or in Cartesian coordinates in units of 2Pi/len. B_VECTOR: in multiples of the reciprocal lattice vectors (b). CART_ANGSTROM: In units of 2

Pi/Angstrom. CART_BOHR: In units of 2

Pi/Bohr.

[

Edit on GitHub

]

VERBOSE

:

logical

=

F



Lone keyword:

T

Usage:

VERBOSE

Mentions:

⭐

K-Points

Verbose output information.

[

Edit on GitHub

]

WAVEFUNCTIONS

:

enum

=

COMPLEX



Usage:

WAVEFUNCTIONS REAL

Valid values:

REAL

Use real wavefunctions (if possible by kpoints specified).

COMPLEX

Use complex wavefunctions (default).

Mentions:

⭐

K-Points

Select whether real or complex wavefunctions should be used when allowed by the k-point set. REAL wavefunctions can only represent Gamma or special k-points and symmetry operations with real Bloch phases. Use COMPLEX for general atomic k-point symmetries with nontrivial phases.

[

Edit on GitHub

]
