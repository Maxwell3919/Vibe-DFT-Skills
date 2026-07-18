# CP2K official manual snapshot: md-thermostat

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/THERMOSTAT.html
- Raw SHA-256: 64bf18c2ecdfb98ac34bc2082c01e823350bc6c5e1cc5a76c1a76d5f9cca6688
- Status: version-matched cached official text; reopen the source for current live verification.

THERMOSTAT



Specify thermostat type and parameters controlling the thermostat.

[

Edit on GitHub

]

Subsections

AD_LANGEVIN

CSVR

DEFINE_REGION

GLE

NOSE

PRINT

Keywords



REGION

TYPE

Keyword descriptions



REGION

:

enum

=

GLOBAL



Usage:

REGION (GLOBAL|MOLECULE|MASSIVE|DEFINED|THERMAL|NONE)

Valid values:

GLOBAL

Apply one thermostat to the whole system (default)

MOLECULE

Apply one thermostat to each molecule kind

MASSIVE

Apply one thermostat to each degree of freedom

DEFINED

Apply one thermostat to each defined region from THERMOSTAT/DEFINE_REGION

THERMAL

Apply one thermostat to each defined region from THERMAL_REGION/DEFINE_REGION

NONE

No thermostat is applied

Determines the region each thermostat is attached to.

[

Edit on GitHub

]

TYPE

:

enum

=

NOSE



Usage:

TYPE NOSE

Valid values:

NOSE

Uses the Nose-Hoover thermostat.

CSVR

Uses the canonical sampling through velocity rescaling.

GLE

Uses GLE thermostat

AD_LANGEVIN

Uses adaptive-Langevin thermostat

Mentions:

⭐

Molecular Dynamics

Specify the thermostat used for the constant temperature ensembles.

[

Edit on GitHub

]
