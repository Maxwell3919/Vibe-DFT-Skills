# CP2K official manual snapshot: hirshfeld

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/HIRSHFELD.html
- Raw SHA-256: bfc28ed4f064c51177b9a88fcf329823057af48dc6a34451e0547cdfb01cfef4
- Status: version-matched cached official text; reopen the source for current live verification.

HIRSHFELD



Controls the printing of the Hirshfeld (spin) population analysis

[

Edit on GitHub

]

Subsections

EACH

Keywords



SECTION_PARAMETERS

ADD_LAST

ATOMIC_RADII

COMMON_ITERATION_LEVELS

FILENAME

LOG_PRINT_KEY

REFERENCE_CHARGE

SELF_CONSISTENT

SHAPE_FUNCTION

USER_RADIUS

__CONTROL_VAL

Keyword descriptions



SECTION_PARAMETERS

:

enum

=

MEDIUM



Lone keyword:

SILENT

Usage:

silent

Valid values:

ON

OFF

SILENT

LOW

MEDIUM

HIGH

DEBUG

Level starting at which this property is printed

[

Edit on GitHub

]

ADD_LAST

:

enum

=

NO



Usage:

ADD_LAST (NO|NUMERIC|SYMBOLIC)

Valid values:

NO

Do not mark last iteration specifically

NUMERIC

Mark last iteration with its iteration number

SYMBOLIC

Mark last iteration with lowercase letter l

If the last iteration should be added, and if it should be marked symbolically (with lowercase letter l) or with the iteration number. Not every iteration level is able to identify the last iteration early enough to be able to output. When this keyword is activated all iteration levels are checked for the last iteration step.

[

Edit on GitHub

]

ATOMIC_RADII

:

real[

]

=

[angstrom]



Usage:

ATOMIC_RADII {real} {real} {real}

Defines custom radii to setup the spherical Gaussians.

[

Edit on GitHub

]

COMMON_ITERATION_LEVELS

:

integer

=

1



Usage:

COMMON_ITERATION_LEVELS

How many iterations levels should be written in the same file (no extra information about the actual iteration level is written to the file)

[

Edit on GitHub

]

FILENAME

:

string

=

__STD_OUT__



Usage:

FILENAME ./filename

controls part of the filename for output. use __STD_OUT__ (exactly as written here) for the screen or standard logger. use filename to obtain projectname-filename. use ./filename to get filename. A middle name (if present), iteration numbers and extension are always added to the filename. if you want to avoid it use =filename, in this case the filename is always exactly as typed. Please note that this can lead to clashes of filenames.

[

Edit on GitHub

]

LOG_PRINT_KEY

:

logical

=

F



Lone keyword:

T

Usage:

LOG_PRINT_KEY

This keywords enables the logger for the print_key (a message is printed on screen everytime data, controlled by this print_key, are written)

[

Edit on GitHub

]

REFERENCE_CHARGE

:

enum

=

ATOMIC



Usage:

REFERENCE_CHARGE {Atomic,Mulliken}

Valid values:

ATOMIC

Use atomic core charges

MULLIKEN

Calculate Mulliken charges

Charge of atomic partitioning function for Hirshfeld method.

[

Edit on GitHub

]

SELF_CONSISTENT

:

logical

=

F



Lone keyword:

T

Usage:

SELF_CONSISTENT yes

Calculate charges from the Hirscheld-I (self_consistent) method. This scales only the full shape function, not the added charge as in the original scheme.

[

Edit on GitHub

]

SHAPE_FUNCTION

:

enum

=

GAUSSIAN



Usage:

SHAPE_FUNCTION {Gaussian,Density}

Valid values:

GAUSSIAN

Single Gaussian with Colvalent radius

DENSITY

Atomic density expanded in multiple Gaussians

Type of shape function used for Hirshfeld partitioning.

[

Edit on GitHub

]

USER_RADIUS

:

logical

=

F



Lone keyword:

T

Usage:

USER_RADIUS yes

Use user defined radii to generate Gaussians. These radii are defined by the keyword ATOMIC_RADII

[

Edit on GitHub

]

__CONTROL_VAL

:

integer

=

8



hidden parameter that controls storage, printing,… of the print_key

[

Edit on GitHub

]
