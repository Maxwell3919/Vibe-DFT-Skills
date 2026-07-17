# KGAMMA

- Official URL: https://www.vasp.at/wiki/KGAMMA
- Page ID: 378
- Revision ID: 35395
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

KGAMMA = [logical]
Default: KGAMMA = .TRUE.

Description: Whether the automatically generated k-point mesh is centered at the [math]\displaystyle{ \Gamma }[/math] point.

If KGAMMA = .TRUE. (default), the k-point mesh is centered at the [math]\displaystyle{ \Gamma }[/math] point, i.e., it always includes the [math]\displaystyle{ \Gamma }[/math] point. If KGAMMA = .FALSE., the mesh is shifted away from the [math]\displaystyle{ \Gamma }[/math] point as in a Monkhorst-Pack grid. The number of k points on the mesh is controlled by KSPACING and KSPACING_OPT.

Important: If a KPOINTS file is present, VASP ignores the KGAMMA and KSPACING tags. Likewise, if a KPOINTS_OPT file is present, VASP ignores KGAMMA and KSPACING_OPT.

Related tags and articles[edit | edit source]

KSPACING, KSPACING_OPT

Workflows that use this tag
