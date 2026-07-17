# KSPACING

- Official URL: https://www.vasp.at/wiki/KSPACING
- Page ID: 379
- Revision ID: 35382
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

KSPACING = [real]
Default: KSPACING = 0.5

Description: Spacing between k points in automatically generated mesh if the KPOINTS file is not present.

KSPACING is the smallest allowed spacing between k points in units of [math]\displaystyle{ \AA^{-1} }[/math]. The number of k points increases when the spacing is decreased.

The number of k points in the direction of the first, second and third reciprocal lattice
vector is determined by [math]\displaystyle{ N_i= \mathrm{max}(1, \mathrm{ceiling}( | \mathbf{b}_i| 2\pi / \mathrm{KSPACING} )) }[/math],
where [math]\displaystyle{ \mathrm{ceiling}( x ) }[/math] returns the least integer that is equal or
larger than [math]\displaystyle{ x }[/math]. Here, [math]\displaystyle{ \mathbf{b}_i }[/math] are the reciprocal lattice vectors [math]\displaystyle{ \mathbf{b}_i \mathbf{a}_j = \delta_{ij} }[/math].

The generated grid is centered at the [math]\displaystyle{ \Gamma }[/math] point if KGAMMA = T (default), i.e., includes the [math]\displaystyle{ \Gamma }[/math] point. For KGAMMA = F, the grid is shifted away from the [math]\displaystyle{ \Gamma }[/math] point as done for Monkhorst-Pack grids.

Mind: The definition of [math]\displaystyle{ N_i }[/math] is not entirely identical with the deprecated automatic k-point generation used in the KPOINTS file. We recommend using the KSPACING tag and avoiding the automatic mode via the KPOINTS file.

Related tags and articles[edit | edit source]

Tags: KGAMMA, KSPACING_OPT

Files: KPOINTS, KPOINTS_OPT

Workflows that use this tag
