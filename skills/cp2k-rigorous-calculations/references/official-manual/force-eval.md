# CP2K official manual snapshot: force-eval

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL.html
- Raw SHA-256: 13342298309800dffc41de24bad9bdf810d1d931cc072eb3ad556069f65bcd58
- Status: version-matched cached official text; reopen the source for current live verification.

FORCE_EVAL



Section can be repeated.

parameters needed to calculate energy and forces and describe the system you want to analyze.

[

Edit on GitHub

]

Subsections

BSSE

DFT

EIP

EMBED

EXTERNAL_POTENTIAL

MIXED

MM

NNP

PRINT

PROPERTIES

PW_DFT

QMMM

RESCALE_FORCES

SUBSYS

Keywords



METHOD

STRESS_TENSOR

Keyword descriptions



METHOD

:

enum

=

QS



Usage:

METHOD

Valid values:

QS

Alias for QUICKSTEP

SIRIUS

PW DFT using the SIRIUS library

FIST

Molecular Mechanics

QMMM

Hybrid quantum classical

EIP

Empirical Interatomic Potential

QUICKSTEP

Electronic structure methods in the Quickstep module, including GPW and GAPW DFT.

NNP

Neural Network Potentials

MIXED

Use a combination of two of the above

EMBED

Perform an embedded calculation

IPI

Receive forces from an i-PI client

Mentions:

⭐

Run a First Calculation

Selects the method used by this FORCE_EVAL section to compute energies, forces, and related properties.

[

Edit on GitHub

]

STRESS_TENSOR

:

enum

=

NONE



Usage:

stress_tensor (NONE|ANALYTICAL|NUMERICAL|DIAGONAL_ANA|DIAGONAL_NUM)

Valid values:

NONE

Do not compute stress tensor

ANALYTICAL

Compute the stress tensor analytically (if available).

NUMERICAL

Compute the stress tensor numerically.

DIAGONAL_ANALYTICAL

Compute the diagonal part only of the stress tensor analytically (if available).

DIAGONAL_NUMERICAL

Compute the diagonal part only of the stress tensor numerically

Mentions:

⭐

Geometry and cell optimization

Controls the calculation of the stress tensor. The combinations defined below are not implemented for all methods.

[

Edit on GitHub

]
