# CP2K official manual snapshot: global-print

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html
- Raw SHA-256: 2bfc8e53be5f601dca3b4248c76b3efd98ff779201dfd48f9cb13a4f4a3dcda2
- Status: version-matched cached official text; reopen the source for current live verification.

PRINT



controls the printing of physical and mathematical constants

[

Edit on GitHub

]

Subsections

EACH

Keywords



SECTION_PARAMETERS

ADD_LAST

BASIC_DATA_TYPES

COMMON_ITERATION_LEVELS

FILENAME

GLOBAL_GAUSSIAN_RNG

LOG_PRINT_KEY

PHYSCON

RNG_CHECK

RNG_MATRICES

SPHERICAL_HARMONICS

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

BASIC_DATA_TYPES

:

logical

=

F



Lone keyword:

T

Controls the printing of the basic data types.

[

Edit on GitHub

]

COMMON_ITERATION_LEVELS

:

integer

=

0

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

GLOBAL_GAUSSIAN_RNG

:

logical

=

F



Lone keyword:

T

Prints the initial status of the global Gaussian (pseudo)random number stream which is mostly used for the velocity initialization

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

PHYSCON

:

logical

=

T



Lone keyword:

T

if the printkey is active prints the physical constants

[

Edit on GitHub

]

RNG_CHECK

:

logical

=

F



Lone keyword:

T

Performs a check of the global (pseudo)random number generator (RNG) and prints the result

[

Edit on GitHub

]

RNG_MATRICES

:

logical

=

F



Lone keyword:

T

Prints the transformation matrices used by the random number generator

[

Edit on GitHub

]

SPHERICAL_HARMONICS

:

integer

=

-1



if the printkey is active prints the spherical harmonics

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
