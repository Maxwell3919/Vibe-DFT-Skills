# CP2K official manual snapshot: subsys

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS.html
- Raw SHA-256: d4fb86bcbf43e2ce2b9046800fa01ea01869f99b866a96654478a61144a62278
- Status: version-matched cached official text; reopen the source for current live verification.

SUBSYS



a subsystem: coordinates, topology, molecules and cell

[

Edit on GitHub

]

Subsections

CELL

COLVAR

COORD

CORE_COORD

CORE_VELOCITY

KIND

MULTIPOLES

PRINT

RNG_INIT

SHELL_COORD

SHELL_VELOCITY

TOPOLOGY

VELOCITY

Keywords



SEED

Keyword descriptions



SEED

:

integer[

]

=

12345



Usage:

SEED {INTEGER} .. {INTEGER}

Initial seed for the (pseudo)random number generator for the Wiener process employed by the Langevin dynamics. Exactly 1 or 6 positive integer values are expected. A single value is replicated to fill up the full seed array with 6 numbers.

[

Edit on GitHub

]
