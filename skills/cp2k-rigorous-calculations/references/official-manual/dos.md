# CP2K official manual snapshot: dos

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html
- Raw SHA-256: 80df0e382ec8485e420117a2fe8227b3c5e660d4e8c87d1a070c1f023d484c55
- Status: version-matched cached official text; reopen the source for current live verification.

DOS



Print density of states (DOS). Projected DOS output can be enabled with PDOS.

[

Edit on GitHub

]

Subsections

CURVE

EACH

LDOS

PDOS

R_LDOS

Keywords



SECTION_PARAMETERS

ADD_LAST

APPEND

COMMON_ITERATION_LEVELS

DELTA_E

FILENAME

LOG_PRINT_KEY

MP_GRID

NDIGITS

NLUMO

OUT_EACH_STATE

__CONTROL_VAL

Keyword descriptions



SECTION_PARAMETERS

:

enum

=

DEBUG

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

APPEND

:

logical

=

F



Lone keyword:

T

Usage:

APPEND

Append the DOS/PDOS obtained at different iterations to the output file. By default the file is overwritten

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

DELTA_E

:

real

=

1.00000000E-003



Usage:

DELTA_E 0.0005

Mentions:

⭐

Density of States

Energy spacing of the DOS/PDOS output grid.

[

Edit on GitHub

]

FILENAME

:

string

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

MP_GRID

:

integer

[

3

]

=

-1



Usage:

MP_GRID {integer} {integer} {integer}

Specify a Monkhorst-Pack grid with which to compute the density of states. Works only for a k-point calculation

[

Edit on GitHub

]

NDIGITS

:

integer

=

6



Specify the number of digits used to print DOS/PDOS values.

[

Edit on GitHub

]

NLUMO

:

integer

=

0



Usage:

NLUMO integer

Mentions:

⭐

Density of States

Number of unoccupied orbitals to include in the DOS/PDOS (-1=all). For OT calculations, the requested virtual orbitals are generated after SCF using the OT eigensolver. For diagonalization calculations, SCF%ADDED_MOS is increased if needed to make the requested unoccupied orbitals available.

[

Edit on GitHub

]

OUT_EACH_STATE

:

integer

=

-1



Aliases:

OUT_EACH_MO

Usage:

OUT_EACH_STATE integer

Output on the status of the calculation every OUT_EACH_MO states. If -1 no output

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
