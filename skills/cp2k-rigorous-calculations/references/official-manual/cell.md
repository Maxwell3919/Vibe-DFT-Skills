# CP2K official manual snapshot: cell

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/CELL.html
- Raw SHA-256: 1407ebd96546241b3e9a339c1429e7d880785adebdd2f3bbd35c32e7391f1f3a
- Status: version-matched cached official text; reopen the source for current live verification.

CELL



Input parameters needed to set up the simulation cell. Simple products and fractions combined with functions of a single number can be used like 2/3, 0.3*COS(60) or -SQRT(3)/2. The functions COS, EXP, LOG, LOG10, SIN, SQRT, and TAN are available.

Cell settings are parsed in the following precedence order:

The external file set by CELL_FILE_NAME with a CELL_FILE_FORMAT;

The lengths and angles of cell vectors set by ABC and ALPHA_BETA_GAMMA;

The vectors set by A, B, C together;

If none above exist, the external file set by TOPOLOGY/COORD_FILE_NAME with suitable TOPOLOGY/COORD_FILE_FORMAT may also be parsed for FORCE_EVAL/SUBSYS/CELL but not for FORCE_EVAL/QMMM/CELL.

[

Edit on GitHub

]

Subsections

CELL_REF

Keywords



A

ABC

ALPHA_BETA_GAMMA

B

C

CANONICALIZE

CELL_FILE_FORMAT

CELL_FILE_NAME

MULTIPLE_UNIT_CELL

PERIODIC

SYMMETRY

Keyword descriptions



A

:

real

[

3

]

=

[angstrom]



Usage:

A 10.000 0.000 0.000

Specify the Cartesian components for the cell vector A. This defines the first column of the h matrix. Ignored if the keywords ABC or CELL_FILE_NAME are used.

[

Edit on GitHub

]

ABC

:

real

[

3

]

=

[angstrom]



Usage:

ABC 10.000 10.000 10.000

Mentions:

⭐

K-Points

Specify the lengths of the cell vectors A, B, and C, which defines the diagonal elements of h matrix for an orthorhombic cell. For non-orthorhombic cells it is possible either to specify the angles ALPHA, BETA, GAMMA via ALPHA_BETA_GAMMA keyword or alternatively use the keywords A, B, and C. The convention is that A lies along the X-axis, B is in the XY plane. Ignored if CELL_FILE_NAME is used.

[

Edit on GitHub

]

ALPHA_BETA_GAMMA

:

real

[

3

]

=

9.00000000E+001

[deg]



Aliases:

ANGLES

Usage:

ALPHA_BETA_GAMMA [deg] 90.0 90.0 120.0

Mentions:

⭐

K-Points

Specify the angles between the vectors A, B and C when using the ABC keyword. The convention is that A lies along the X-axis, B is in the XY plane. ALPHA is the angle between B and C, BETA is the angle between A and C and GAMMA is the angle between A and B.

[

Edit on GitHub

]

B

:

real

[

3

]

=

[angstrom]



Usage:

B 0.000 10.000 0.000

Specify the Cartesian components for the cell vector B. This defines the second column of the h matrix. Ignored if the keywords ABC or CELL_FILE_NAME are used.

[

Edit on GitHub

]

C

:

real

[

3

]

=

[angstrom]



Usage:

C 0.000 0.000 10.000

Specify the Cartesian components for the cell vector C. This defines the third column of the h matrix. Ignored if the keywords ABC or CELL_FILE_NAME are used.

[

Edit on GitHub

]

CANONICALIZE

:

enum

=

AUTO



Lone keyword:

TRUE

Usage:

CANONICALIZE AUTO

Valid values:

AUTO

Keep the input orientation unless canonicalization is unambiguously safe

TRUE

Explicitly canonicalize the input cell

FALSE

Keep the input cell orientation

T

Alias for TRUE

F

Alias for FALSE

.TRUE.

Alias for TRUE

.FALSE.

Alias for FALSE

Policy for transforming a general input cell to CP2K’s internal convention that A lies along the X-axis and B is in the XY plane. AUTO is conservative and keeps the input orientation when a silent transformation could affect Cartesian or direction-dependent input. TRUE explicitly requests canonicalization and transforms supported cell-dependent input. FALSE always keeps the input orientation.

[

Edit on GitHub

]

CELL_FILE_FORMAT

:

enum

=

CP2K



Usage:

CELL_FILE_FORMAT (CP2K|CIF|XSC|EXTXYZ|XYZ|PDB)

Valid values:

CP2K

Cell info in the CP2K native format

CIF

Cell info from CIF file (from fields

_cell_length_a

or

_cell.length_a

, etc)

XSC

Cell info in the XSC format (NAMD)

EXTXYZ

Cell info as

lattice=...

field in the comment line of Extended XYZ format

XYZ

Alias for Extended XYZ

PDB

Cell info in the

CRYST1

record of PDB format

Format of the external file from which cell is parsed. If the format specifies a cell by lengths and angles of three vectors, then a cell matrix is constructed with the convention that A lies along the X-axis, B is in the XY plane. ALPHA is the angle between B and C, BETA is the angle between A and C, and GAMMA is the angle between A and B.

[

Edit on GitHub

]

CELL_FILE_NAME

:

string



Usage:

CELL_FILE_NAME

The external file from which cell is parsed

[

Edit on GitHub

]

MULTIPLE_UNIT_CELL

:

integer

[

3

]

=

1



Usage:

MULTIPLE_UNIT_CELL 1 1 1

Specifies the numbers of repetition in space (X, Y, Z) of the defined cell, assuming it as a unit cell. This keyword affects only the CELL specification. The same keyword in SUBSYS%TOPOLOGY%MULTIPLE_UNIT_CELL should be modified in order to affect the coordinates specification.

[

Edit on GitHub

]

PERIODIC

:

enum

=

XYZ



Usage:

PERIODIC (x|y|z|xy|xz|yz|xyz|none)

Valid values:

X

Y

Z

XY

XZ

YZ

XYZ

NONE

Specify the directions for which periodic boundary conditions (PBC) will be applied. Important notice: This applies to the generation of the pair lists as well as to the application of the PBCs to positions. See the POISSON section to specify the periodicity used for the electrostatics. Typically the settings should be the same.

[

Edit on GitHub

]

SYMMETRY

:

enum

=

NONE



Usage:

SYMMETRY monoclinic

Valid values:

NONE

No cell symmetry

TRICLINIC

Triclinic (a ≠ b ≠ c ≠ a, α ≠ β ≠ γ ≠ α ≠ 90°)

MONOCLINIC

Monoclinic (a ≠ b ≠ c, α = γ = 90°, β ≠ 90°)

MONOCLINIC_GAMMA_AB

Monoclinic (a = b ≠ c, α = β = 90°, γ ≠ 90°)

ORTHORHOMBIC

Orthorhombic (a ≠ b ≠ c, α = β = γ = 90°)

TETRAGONAL_AB

Tetragonal (a = b ≠ c, α = β = γ = 90°)

TETRAGONAL_AC

Tetragonal (a = c ≠ b, α = β = γ = 90°)

TETRAGONAL_BC

Tetragonal (a ≠ b = c, α = β = γ = 90°)

TETRAGONAL

Tetragonal (alias for TETRAGONAL_AB)

RHOMBOHEDRAL

Rhombohedral (a = b = c, α = β = γ ≠ 90°)

HEXAGONAL

Hexagonal (alias for HEXAGONAL_GAMMA_60)

HEXAGONAL_GAMMA_60

Hexagonal (a = b ≠ c, α = β = 90°, γ = 60°)

HEXAGONAL_GAMMA_120

Hexagonal (a = b ≠ c, α = β = 90°, γ = 120°)

CUBIC

Cubic (a = b = c, α = β = γ = 90°)

Mentions:

⭐

Geometry and cell optimization

Imposes an initial cell symmetry, according to the convention that A lies along the X-axis, B is in the XY plane. After the input cell information is parsed, the symmetry is enforced by reconstructing the cell matrix from lengths and angles of the cell vectors, taking averages if necessary. This process does not affect input atomic coordinates; in case a space group is to be detected and preserved for an optimization task, atomic coordinates should correspond to cell vectors already obeying the convention mentioned above.

[

Edit on GitHub

]
