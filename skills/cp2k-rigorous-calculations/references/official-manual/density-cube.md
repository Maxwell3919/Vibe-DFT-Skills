# CP2K official manual snapshot: density-cube

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE.html
- Raw SHA-256: 14be00741ca24e39694caa174c9d862cdf1c744c2af14c89eaaa34409281f88a
- Status: version-matched cached official text; reopen the source for current live verification.

E_DENSITY_CUBE



Controls the printing of cube files with the electronic density and, for LSD calculations, the spin density.

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

DENSITY_INCLUDE

FILENAME

LOG_PRINT_KEY

NGAUSS

STRIDE

XRD_INTERFACE

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

DENSITY_INCLUDE

:

enum

=

TOTAL_HARD_APPROX



Usage:

DENSITY_INCLUDE TOTAL_HARD_APPROX

Valid values:

TOTAL_HARD_APPROX

Print (hard+soft) density where the hard components shape is approximated

TOTAL_DENSITY

Print (hard+soft) density. Only has an effect if PAW atoms are present. NOTE: The total in real space might exhibit unphysical features like spikes due to the finite and thus truncated g vector

SOFT_DENSITY

Print only the soft density

Which parts of the density to include. In GAPW the electronic density is divided into a hard and a soft component, and the default (TOTAL_HARD_APPROX) is to approximate the hard density as a spherical gaussian and to print the smooth density accurately. This avoids potential artefacts originating from the hard density. If the TOTAL_DENSITY keyword is used the hard density will be computed more accurately but may introduce non-physical features. The SOFT_DENSITY keyword will lead to only the soft density being printed. In GPW these options have no effect and the cube file will only contain the valence electron density.

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

NGAUSS

:

integer

=

12



Usage:

NGAUSS 10

Number of Gaussian functions used in the expansion of atomic (core) density

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

The stride (X,Y,Z) used to write the cube file (larger values result in smaller cube files). You can provide 3 numbers (for X,Y,Z) or 1 number valid for all components.

[

Edit on GitHub

]

XRD_INTERFACE

:

logical

=

F



Lone keyword:

T

It activates the print out of exponents and coefficients for the Gaussian expansion of the core densities, based on atom calculations for each kind. The resulting core dansities are needed to compute the form factors. If GAPW the local densities are also given in terms of a Gaussian expansion, by fitting the difference between local-fhard and local-soft density for each atom. In this case the keyword SOFT_DENSITY is enabled.

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
