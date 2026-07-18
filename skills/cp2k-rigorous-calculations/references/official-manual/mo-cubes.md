# CP2K official manual snapshot: mo-cubes

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/MO_CUBES.html
- Raw SHA-256: 474a5074befe69d53a7d245866f31555374de802e8869d00e9fe6f19882ebbd6
- Status: version-matched cached official text; reopen the source for current live verification.

MO_CUBES



Controls the printing of the molecular orbitals (MOs) as cube files. It can be used during a Real Time calculation to print the MOs. In this case, the density corresponding to the time dependent MO is printed instead of the wave-function.

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

FILENAME

HOMO_LIST

LOG_PRINT_KEY

MAX_FILE_SIZE_MB

NHOMO

NLUMO

STRIDE

WRITE_CUBE

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

HOMO_LIST

:

integer[

]



Keyword can be repeated.

Usage:

HOMO_LIST {integer} {integer} .. {integer}

Mentions:

⭐

Molecular orbitals output

If the printkey is activated controls the index of homos dumped as openPMD, eigenvalues are always all dumped. It overrides nhomo.

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

MAX_FILE_SIZE_MB

:

real

=

0.00000000E+000



Usage:

MAX_FILE_SIZE_MB 1.5

Mentions:

⭐

Molecular orbitals output

Limits the size of the cube file by choosing a suitable stride. Zero means no limit.

[

Edit on GitHub

]

NHOMO

:

integer

=

1



Mentions:

⭐

Molecular orbitals output

If the printkey is activated controls the number of homos that dumped as cube (-1=all), eigenvalues are always all dumped

[

Edit on GitHub

]

NLUMO

:

integer

=

0



Mentions:

⭐

Molecular orbitals output

If the printkey is activated controls the number of lumos that are printed and dumped as cube (-1=all)

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

STRIDE 1 1 1

Mentions:

⭐

Molecular orbitals output

The stride (X,Y,Z) used to write the cube file (larger values result in smaller cube files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components.

[

Edit on GitHub

]

WRITE_CUBE

:

logical

=

T



Lone keyword:

T

Mentions:

⭐

Molecular orbitals output

If the MO cube file should be written. If false, the eigenvalues are still computed. Can also be useful in combination with STM calculations

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
