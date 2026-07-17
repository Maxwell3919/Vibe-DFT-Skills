# LDAUU

- Official URL: https://www.vasp.at/wiki/LDAUU
- Page ID: 150
- Revision ID: 36504
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LDAUU = [real array]
Default: LDAUU = NTYP*0.0

Description: Sets the effective on-site Coulomb interactions (eV).

LDAUU specifies the strength of the effective on-site Coulomb interactions in eV. It must hold one value for each atomic species.

Warning: The total energy will depend on the parameters [math]\displaystyle{ U }[/math] (LDAUU) and [math]\displaystyle{ J }[/math] (LDAUJ). It is, therefore, not meaningful to compare the total energies resulting from calculations with different [math]\displaystyle{ U }[/math] and/or [math]\displaystyle{ J }[/math]; or [math]\displaystyle{ U-J }[/math] in the case of Dudarev's approach (LDAUTYPE=2).

Mind: For LDAUTYPE=3, the LDAUU and LDAUJ tags specify the strength (in eV) of the spherical potential acting on the spin-up and spin-down manifolds, respectively.

Related tags and articles[edit | edit source]

LDAU,
LDAUTYPE,
LDAUL,
LDAUJ,
LDAUPRINT,
LMAXMIX

Examples that use this tag
