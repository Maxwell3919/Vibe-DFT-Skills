# CP2K official manual snapshot: coord

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/COORD.html
- Raw SHA-256: 31e8b272ac02b3589e9c049c4836adebfcaa320cdfe5fecef2ed49a89cc24962
- Status: version-matched cached official text; reopen the source for current live verification.

COORD



The coordinates for simple systems (like small QM cells) are specified here by default using explicit XYZ coordinates. Simple products and fractions combined with functions of a single number can be used like 2/3, 0.3*COS(60) or -SQRT(3)/2. More complex systems should be given via an external coordinate file in the SUBSYS%TOPOLOGY section.

[

Edit on GitHub

]

Keywords



DEFAULT_KEYWORD

SCALED

UNIT

Keyword descriptions



DEFAULT_KEYWORD

:

string



Keyword can be repeated.

Usage:

{{String} {Real} {Real} {Real} {String}}

The atomic coordinates in the format:

ATOMIC_KIND

X

Y

Z

MOLNAME

The

MOLNAME

is optional. If not provided the molecule name is internally created. All other fields after

MOLNAME

are simply ignored.

[

Edit on GitHub

]

SCALED

:

logical

=

F



Lone keyword:

T

Usage:

SCALED F

Specify if the coordinates in input are scaled. When true, the coordinates are given in multiples of the lattice vectors.

[

Edit on GitHub

]

UNIT

:

string

=

angstrom



Usage:

UNIT angstrom

Specify the unit of measurement for the coordinates in inputAll available CP2K units can be used.

[

Edit on GitHub

]
