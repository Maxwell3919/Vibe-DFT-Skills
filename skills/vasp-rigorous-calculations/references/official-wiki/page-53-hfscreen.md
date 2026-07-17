# HFSCREEN

- Official URL: https://www.vasp.at/wiki/HFSCREEN
- Page ID: 53
- Revision ID: 31117
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

HFSCREEN = [real]
Default: HFSCREEN = 0 (none)

Description: HFSCREEN (in Å-1) specifies the range-separation parameter in range-separated hybrid functionals.

If LHFCALC=.TRUE. and GGA=PE (PBE functional), attributing a value to HFSCREEN will switch from the PBE0 functional to, e.g., the closely related HSE03 (HFSCREEN=0.3) or HSE06 (HFSCREEN=0.2) functionals. It also needs to be set for dielectric-dependent hybrid functionals (DDH) and doubly screened hybrid (DSH) functionals, see LMODELHF.

Mind: HFSCREEN can be used only when GGA=PE, PS or CA. The other GGA and METAGGA functionals have no screened version available in VASP.

Related tags and articles[edit | edit source]

LMODELHF,
AEXX,
ALDAX,
ALDAC,
AGGAX,
AGGAC,
LTHOMAS,
LRHFCALC,
List of hybrid functionals,
Hybrid functionals: formalism

Examples that use this tag
