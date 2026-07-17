# EMIN

- Official URL: https://www.vasp.at/wiki/EMIN
- Page ID: 258
- Revision ID: 26951
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

EMIN = [real]

Default: EMIN

= lowest KS eigenvalue - [math]\displaystyle{ \Delta }[/math]

Description: EMIN specifies the lower boundary of the energy range for the evaluation of the electronic density of states (DOS).

The DOS is evaluated each NBLOCK steps, DOSCAR is updated each NBLOCK*KBLOCK steps.

Tip: Set EMIN to a value larger than EMAX, if you are not sure where the region of interest lies.

Related tags and articles[edit | edit source]

EMAX, NEDOS,
DOSCAR

Examples that use this tag
