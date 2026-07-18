# CP2K official manual snapshot: band-optimizer

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND.html
- Raw SHA-256: cf8ac3605c671b35bbd72bd385f17ee22626779d431be6973d4c4430f43150c8
- Status: version-matched cached official text; reopen the source for current live verification.

OPTIMIZE_BAND



Section can be repeated.

Specify the optimization method for the band

[

Edit on GitHub

]

Subsections

DIIS

MD

Keywords



OPTIMIZE_END_POINTS

OPT_TYPE

Keyword descriptions



OPTIMIZE_END_POINTS

:

logical

=

F



Lone keyword:

T

If both end points of the band are also optimized alongside the rest of replica. This may be set to .TRUE. if both end points have already been optimized with the same FORCE_EVAL, in which case the force on both end points will be reset to 0 on each step. Please note that both end points will always be included in NUMBER_OF_REPLICA and get NPROC_REP processors allocated each for calculation in the same way as the rest of replica, regardless of this setting.

[

Edit on GitHub

]

OPT_TYPE

:

enum

=

DIIS



Usage:

OPT_TYPE (MD|DIIS)

Valid values:

MD

Molecular dynamics-based optimizer

DIIS

Coupled steepest descent / direct inversion in the iterative subspace

Mentions:

⭐

Troubleshooting

Specifies the type optimizer used for the band

[

Edit on GitHub

]
