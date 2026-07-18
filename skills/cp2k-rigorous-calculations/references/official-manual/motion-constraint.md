# CP2K official manual snapshot: motion-constraint

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html
- Raw SHA-256: 9b4559470ae890642b072e8b49f40f876e52d3d3a536c0c1f8115cf8b14be30b
- Status: version-matched cached official text; reopen the source for current live verification.

CONSTRAINT



Section specifying information regarding how to impose constraints on the system.

[

Edit on GitHub

]

Subsections

COLLECTIVE

COLVAR_RESTART

CONSTRAINT_INFO

FIXED_ATOMS

FIX_ATOM_RESTART

G3X3

G4X6

HBONDS

LAGRANGE_MULTIPLIERS

VIRTUAL_SITE

Keywords



CONSTRAINT_INIT

PIMD_BEADWISE_CONSTRAINT

ROLL_TOLERANCE

SHAKE_TOLERANCE

Keyword descriptions



CONSTRAINT_INIT

:

logical

=

F



Lone keyword:

T

Usage:

CONSTRAINT_INIT

Apply constraints to the initial position and velocities. Default is to apply constraints only after the first MD step.

[

Edit on GitHub

]

PIMD_BEADWISE_CONSTRAINT

:

logical

=

F



Lone keyword:

T

Usage:

PIMD_BEADWISE_CONSTRAINT

Apply beadwise constraints to PIMD.

[

Edit on GitHub

]

ROLL_TOLERANCE

:

real

=

1.00000000E-010

[internal_cp2k]



Aliases:

ROLL_TOL ,ROLL

Usage:

ROLL_TOLERANCE

Set the tolerance for the roll constraint algorithm.

[

Edit on GitHub

]

SHAKE_TOLERANCE

:

real

=

1.00000000E-006

[internal_cp2k]



Aliases:

SHAKE_TOL ,SHAKE

Usage:

SHAKE_TOLERANCE

Set the tolerance for the shake/rattle constraint algorithm.

[

Edit on GitHub

]
