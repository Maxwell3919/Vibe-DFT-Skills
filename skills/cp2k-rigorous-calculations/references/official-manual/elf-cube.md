# CP2K official manual snapshot: elf-cube

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/ELF_CUBE.html
- Raw SHA-256: d23c739afbd98a25058ee9c2f0689ea85de3038963f9f7d910f8f51fb98dcad0
- Status: version-matched cached official text; reopen the source for current live verification.

ELF_CUBE



Controls printing of cube files with the electron localization function (ELF). Note that the value of ELF is defined between 0 and 1: Pauli kinetic energy density normalized by the kinetic energy density of a uniform el. gas of same density.

[

Edit on GitHub

]

Subsections

EACH

Keywords



SECTION_PARAMETERS

ADD_LAST

APPEND

COMMON_ITERATION_LEVELS

DENSITY_CUTOFF

FILENAME

LOG_PRINT_KEY

STRIDE

__CONTROL_VAL

Keyword descriptions



SECTION_PARAMETERS

:

enum

=

HIGH

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

append the cube files when they already exist

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

DENSITY_CUTOFF

:

real

=

1.00000000E-010



Usage:

density_cutoff 0.0001

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

STRIDE

:

integer[

]

=

2



Usage:

STRIDE 2 2 2

The stride (X,Y,Z) used to write the file (larger values result in smaller files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components.

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
