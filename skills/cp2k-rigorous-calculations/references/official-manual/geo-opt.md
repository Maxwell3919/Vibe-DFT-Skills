# CP2K official manual snapshot: geo-opt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/GEO_OPT.html
- Raw SHA-256: 70c0ee49a151de7bd6bd03d647cbaf2968a3981adb701f7c10d300d932712434
- Status: version-matched cached official text; reopen the source for current live verification.

GEO_OPT



This section sets the environment of the geometry optimizer.

[

Edit on GitHub

]

Subsections

BFGS

CG

LBFGS

PRINT

TRANSITION_STATE

Keywords



EPS_SYMMETRY

KEEP_SPACE_GROUP

MAX_DR

MAX_FORCE

MAX_ITER

OPTIMIZER

RMS_DR

RMS_FORCE

SHOW_SPACE_GROUP

SPGR_PRINT_ATOMS

STEP_START_VAL

SYMM_EXCLUDE_RANGE

SYMM_REDUCTION

TYPE

Keyword descriptions



EPS_SYMMETRY

:

real

=

1.00000000E-004



Usage:

EPS_SYMMETRY {REAL}

Accuracy for space group determination. EPS_SYMMETRY is dimensionless. Roughly speaking, two scaled (fractional) atomic positions v1, v2 are considered identical if |v1 - v2| < EPS_SYMMETRY.

[

Edit on GitHub

]

KEEP_SPACE_GROUP

:

logical

=

F



Lone keyword:

T

Usage:

KEEP_SPACE_GROUP .TRUE.

Mentions:

⭐

K-Points

, ⭐

Geometry and cell optimization

Detect space group of the system and preserve it during optimization. The space group symmetry is applied to coordinates, forces, and the stress tensor. It works for supercell. It does not affect/reduce computational cost. Use EPS_SYMMETRY to adjust the detection threshold.

[

Edit on GitHub

]

MAX_DR

:

real

=

3.00000000E-003

[bohr]



Usage:

MAX_DR {real}

Convergence criterion for the maximum geometry change between the current and the last optimizer iteration.

[

Edit on GitHub

]

MAX_FORCE

:

real

=

4.50000000E-004

[bohr^-1*hartree]



Usage:

MAX_FORCE {real}

Mentions:

⭐

Geometry and cell optimization

, ⭐

Simulating Vibronic Effects in Optical Spectra

Convergence criterion for the maximum force component of the current configuration.

[

Edit on GitHub

]

MAX_ITER

:

integer

=

200



Usage:

MAX_ITER {integer}

Mentions:

⭐

Geometry and cell optimization

Specifies the maximum number of geometry optimization steps. One step might imply several force evaluations for the CG and LBFGS optimizers.

[

Edit on GitHub

]

OPTIMIZER

:

enum

=

BFGS



Aliases:

MINIMIZER

Usage:

OPTIMIZER {BFGS|LBFGS|CG}

Valid values:

BFGS

Most efficient minimizer, but only for ‘small’ systems, as it relies on diagonalization of a full Hessian matrix

LBFGS

Limited-memory variant of BFGS suitable for large systems. Not as well fine-tuned but can be more robust.

CG

conjugate gradients, robust minimizer (depending on the line search) also OK for large systems

References:

Byrd1995

Mentions:

⭐

Geometry and cell optimization

Specify which method to use to perform a geometry optimization.

[

Edit on GitHub

]

RMS_DR

:

real

=

1.50000000E-003

[bohr]



Usage:

RMS_DR {real}

Mentions:

⭐

Geometry and cell optimization

Convergence criterion for the root mean square (RMS) geometry change between the current and the last optimizer iteration.

[

Edit on GitHub

]

RMS_FORCE

:

real

=

3.00000000E-004

[bohr^-1*hartree]



Usage:

RMS_FORCE {real}

Convergence criterion for the root mean square (RMS) force of the current configuration.

[

Edit on GitHub

]

SHOW_SPACE_GROUP

:

logical

=

F



Lone keyword:

T

Usage:

SHOW_SPACE_GROUP .TRUE.

Detect and show space group of the system after optimization. It works for supercell. It does not affect/reduce computational cost. Use EPS_SYMMETRY to adjust the detection threshold.

[

Edit on GitHub

]

SPGR_PRINT_ATOMS

:

logical

=

F



Lone keyword:

T

Print equivalent atoms list for each space group symmetry operation.

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

step_start_val

The starting step value for the GEO_OPT module.

[

Edit on GitHub

]

SYMM_EXCLUDE_RANGE

:

integer

[

2

]



Keyword can be repeated.

Usage:

SYMM_EXCLUDE_RANGE {Int} {Int}

Range of atoms to exclude from space group symmetry. These atoms are excluded from both identification and enforcement. This keyword can be repeated.

[

Edit on GitHub

]

SYMM_REDUCTION

:

real

[

3

]

=

0.00000000E+000



Usage:

SYMM_REDUCTION 0.0 0.0 0.0

Direction of the external static electric field. Some symmetry operations are not compatible with the direction of an electric field. These operations are used when enforcing the space group.

[

Edit on GitHub

]

TYPE

:

enum

=

MINIMIZATION



Usage:

TYPE (MINIMIZATION|TRANSITION_STATE)

Valid values:

MINIMIZATION

Performs a geometry minimization.

TRANSITION_STATE

Performs a transition state optimization.

Mentions:

⭐

Geometry and cell optimization

Specify which kind of geometry optimization to perform

[

Edit on GitHub

]
