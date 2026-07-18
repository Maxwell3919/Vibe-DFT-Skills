# CP2K official manual snapshot: outer-scf

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/OUTER_SCF.html
- Raw SHA-256: b54632d02f2a1290cff9f07157ca744d99cf5217910f71a8d472e1fb0e4f5711
- Status: version-matched cached official text; reopen the source for current live verification.

OUTER_SCF



Controls an outer SCF loop, often used to stabilize difficult OT convergence, constraints, or other variables wrapped around the inner SCF cycle.

[

Edit on GitHub

]

Subsections

CDFT_OPT

Keywords



SECTION_PARAMETERS

BISECT_TRUST_COUNT

DIIS_BUFFER_LENGTH

EPS_SCF

EXTRAPOLATION_ORDER

MAX_SCF

OPTIMIZER

STEP_SIZE

TYPE

Keyword descriptions



SECTION_PARAMETERS

:

logical

=

F



Lone keyword:

T

Usage:

&OUTER_SCF ON

Activates the outer SCF loop.

[

Edit on GitHub

]

BISECT_TRUST_COUNT

:

integer

=

10



Usage:

BISECT_TRUST_COUNT 5

Maximum number of times the same point will be used in bisection, a small number guards against the effect of wrongly converged states.

[

Edit on GitHub

]

DIIS_BUFFER_LENGTH

:

integer

=

3



Usage:

DIIS_BUFFER_LENGTH 5

Maximum number of DIIS vectors used

[

Edit on GitHub

]

EPS_SCF

:

real

=

1.00000000E-005



Usage:

EPS_SCF 1.0E-6

The target gradient of the outer SCF variables. Notice that the EPS_SCF of the inner loop also determines the value that can be reached in the outer loop, typically EPS_SCF of the outer loop must be smaller than or equal to EPS_SCF of the inner loop.

[

Edit on GitHub

]

EXTRAPOLATION_ORDER

:

integer

=

3



Usage:

EXTRAPOLATION_ORDER 5

Number of past states used in the extrapolation of the variables during e.g. MD

[

Edit on GitHub

]

MAX_SCF

:

integer

=

50



Usage:

MAX_SCF 20

Mentions:

⭐

How to make a SCF run converge

Maximum number of outer SCF loops.

[

Edit on GitHub

]

OPTIMIZER

:

enum

=

NONE



Usage:

OPTIMIZER SD

Valid values:

SD

Takes steps in the direction of the gradient, multiplied by step_size

DIIS

Uses a Direct Inversion in the Iterative Subspace method

NONE

Do nothing, useful only with the none type

BISECT

Bisection of the gradient, useful for difficult one dimensional cases

BROYDEN

Broyden’s method. Variant defined in BROYDEN_TYPE.

NEWTON

Newton’s method. Only compatible with CDFT constraints.

SECANT

Secant method. Only for one dimensional cases. See Broyden for multidimensional cases.

NEWTON_LS

Newton’s method with backtracking line search to find the optimal step size. Only compatible with CDFT constraints. Starts from the regular Newton solution and successively reduces the step size until the L2 norm of the CDFT gradient decreases or MAX_LS steps is reached. Potentially very expensive because each iteration performs a full SCF calculation.

Method used to bring the outer loop to a stationary point

[

Edit on GitHub

]

STEP_SIZE

:

real

=

5.00000000E-001



Usage:

STEP_SIZE -1.0

The initial step_size used in the optimizer (currently steepest descent). Note that in cases where a sadle point is sought for (constrained DFT), this can be negative. For Newton and Broyden optimizers, use a value less/higher than the default 1.0 (in absolute value, the sign is not significant) to active an under/overrelaxed optimizer.

[

Edit on GitHub

]

TYPE

:

enum

=

NONE



Usage:

TYPE DDAPC_CONSTRAINT

Valid values:

DDAPC_CONSTRAINT

Enforce a constraint on the DDAPC, requires the corresponding section

S2_CONSTRAINT

Enforce a constraint on the S2, requires the corresponding section

BASIS_CENTER_OPT

Optimize positions of basis functions, if atom types FLOATING_BASIS_CENTER are defined

CDFT_CONSTRAINT

Enforce a constraint on a generic CDFT weight population. Requires the corresponding section QS&CDFT which determines the type of weight used.

NONE

Do nothing in the outer loop, useful for resetting the inner loop,

Specifies which kind of outer SCF should be employed

[

Edit on GitHub

]
