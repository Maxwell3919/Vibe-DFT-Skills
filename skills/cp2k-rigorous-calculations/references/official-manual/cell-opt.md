# CP2K official manual snapshot: cell-opt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CELL_OPT.html
- Raw SHA-256: d1e0a0b3d2e46b929b4fae44d6e9fbfcef6e065180fe56b8a9d291ef704c25d0
- Status: version-matched cached official text; reopen the source for current live verification.

CELL_OPT



This section sets the environment for the optimization of the simulation cell. As is noted in FORCE_EVAL/SUBSYS/CELL, the program convention is that the first cell vector A lies along the X-axis and the second cell vector B is in the XY plane, such that the cell vector matrix is a lower triangle. There is no complete, official algorithm support and/or tests for updating the three upper triangular components during a cell optimization; please prepare input accordingly with these three components precisely 0 even for cases like the primitive rhombohedral cell of the FCC lattice.

[

Edit on GitHub

]

Subsections

BFGS

CG

LBFGS

PRINT

Keywords



CONSTRAINT

EPS_SYMMETRY

EXTERNAL_PRESSURE

KEEP_ANGLES

KEEP_SPACE_GROUP

KEEP_SYMMETRY

KEEP_VOLUME

MAX_DR

MAX_FORCE

MAX_ITER

OPTIMIZER

PRESSURE_TOLERANCE

RMS_DR

RMS_FORCE

SHOW_SPACE_GROUP

SPGR_PRINT_ATOMS

STEP_START_VAL

SYMM_EXCLUDE_RANGE

SYMM_REDUCTION

Keyword descriptions



CONSTRAINT

:

enum

=

NONE



Usage:

CONSTRAINT (none|x|y|z|xy|xz|yz)

Valid values:

NONE

Fix nothing

X

Fix only x component

Y

Fix only y component

Z

Fix only z component

XY

Fix x and y component

XZ

Fix x and z component

YZ

Fix y and z component

Mentions:

⭐

Geometry and cell optimization

Imposes a constraint on the pressure tensor by fixing the specified cell components.

[

Edit on GitHub

]

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

EXTERNAL_PRESSURE

:

real[

]

=

1.00000000E+002

0.00000000E+000

1.00000000E+002

0.00000000E+000

1.00000000E+002

[bar]



Usage:

EXTERNAL_PRESSURE {REAL} .. {REAL}

Mentions:

⭐

Geometry and cell optimization

Specifies the external pressure (1 value or the full 9 components of the pressure tensor) applied during the cell optimization.

[

Edit on GitHub

]

KEEP_ANGLES

:

logical

=

F



Lone keyword:

T

Usage:

KEEP_ANGLES TRUE

Mentions:

⭐

Geometry and cell optimization

Keep angles between the cell vectors constant, but allow the lengths of the cell vectors to change independently during cell optimization. This is implemented by projecting out the components of angles in the cell gradient before the cell is updated. Albeit general, this is most useful for triclinic cells; to enforce higher symmetry, see KEEP_SYMMETRY.

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

Geometry and cell optimization

Detect space group of the system and preserve it during optimization. The space group symmetry is applied to coordinates, forces, and the stress tensor. It works for supercell. It does not affect/reduce computational cost. Use EPS_SYMMETRY to adjust the detection threshold.

[

Edit on GitHub

]

KEEP_SYMMETRY

:

logical

=

F



Lone keyword:

T

Usage:

KEEP_SYMMETRY TRUE

Mentions:

⭐

K-Points

, ⭐

Geometry and cell optimization

Keep the requested initial cell symmetry as specified in the FORCE_EVAL/SUBSYS/CELL section during cell optimization. This is implemented by removing symmetry-breaking components and taking averages of components if necessary in the cell gradient before the cell is updated. To enforce the space group (which requires spglib package), see KEEP_SPACE_GROUP.

[

Edit on GitHub

]

KEEP_VOLUME

:

logical

=

F



Lone keyword:

T

Usage:

KEEP_VOLUME TRUE

Mentions:

⭐

Geometry and cell optimization

Keep the volume of the cell constant during cell optimization. This is implemented by comparing the cell volumes and scaling the new cell vectors just before updating the cell information, and can be used together with KEEP_ANGLES or KEEP_SYMMETRY.

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

Troubleshooting

Specify which method to use to perform a geometry optimization.

[

Edit on GitHub

]

PRESSURE_TOLERANCE

:

real

=

1.00000000E+002

[bar]



Usage:

PRESSURE_TOLERANCE {REAL}

Mentions:

⭐

Geometry and cell optimization

Specifies the Pressure tolerance (compared to the external pressure) to achieve during the cell optimization.

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

The starting step value for the CELL_OPT module.

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
