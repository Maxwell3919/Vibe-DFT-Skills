# CP2K official manual snapshot: vdw-potential

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/VDW_POTENTIAL.html
- Raw SHA-256: 589c30fe8a9e7ecbc858d26ca95f5979063adca22f4813a9fc88b6748f3fe64d
- Status: version-matched cached official text; reopen the source for current live verification.

VDW_POTENTIAL



References:

Grimme2006

,

Tran2013

This section combines all possible additional dispersion corrections to the normal XC functionals. This can be more functionals or simple empirical pair potentials.

[

Edit on GitHub

]

Subsections

NON_LOCAL

PAIR_POTENTIAL

Keywords



POTENTIAL_TYPE

Keyword descriptions



POTENTIAL_TYPE

:

enum

=

NONE



Aliases:

DISPERSION_FUNCTIONAL

Usage:

POTENTIAL_TYPE (NONE|PAIR_POTENTIAL|NON_LOCAL)

Valid values:

NONE

No dispersion/van der Waals functional.

PAIR_POTENTIAL

Pair potential van der Waals density functional, including Grimme’s empirical DFT-D methods.

NON_LOCAL

Nonlocal van der Waals density functional; more rigorous in principle, but significantly more time-consuming.

Type of dispersion/vdW functional or potential to use

[

Edit on GitHub

]
