# CP2K official manual snapshot: mulliken

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MULLIKEN.html
- Raw SHA-256: 4ce30f5f82d0e6097dfe56488ec9d469e487d24ca3ccd3b471a873aea913b745
- Status: version-matched cached official text; reopen the source for current live verification.

MULLIKEN



Controls the printing of the Mulliken (spin) population analysis

[

Edit on GitHub

]

Subsections

EACH

Keywords



SECTION_PARAMETERS

ADD_LAST

COMMON_ITERATION_LEVELS

FILENAME

LOG_PRINT_KEY

PRINT_ALL

PRINT_GOP

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

PRINT_ALL

:

logical

=

F



Lone keyword:

T

Usage:

PRINT_ALL yes

Print all information including the full net AO and overlap population matrix

[

Edit on GitHub

]

PRINT_GOP

:

logical

=

F



Lone keyword:

T

Usage:

PRINT_GOP yes

Print the gross orbital populations (GOP) in addition to the gross atomic populations (GAP) and net charges

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
