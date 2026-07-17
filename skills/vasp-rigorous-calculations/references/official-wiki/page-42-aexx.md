# AEXX

- Official URL: https://www.vasp.at/wiki/AEXX
- Page ID: 42
- Revision ID: 33504
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

AEXX = [real]

Default: AEXX

= 0.25

if LHFCALC=.TRUE. .AND. LRHFCALC=.FALSE.

= 1

if LRHFCALC=.TRUE.

= 0

if LHFCALC=.FALSE.

Description: AEXX specifies the fraction of exact exchange in a Hartree-Fock-type/hybrid-functional calculation.

Mind:

- For versions of VASP prior to 6.4.0, ALDAX was constrained to be equal to 1.0-AEXX. This constraint is lifted since VASP.6.4.0.

- For AEXX=1.0, VASP switches off correlation by default (ALDAC=0.0, AGGAC=0.0, and AMGGAC=0.0) and thus runs a full Hartree-Fock calculation.

Related tags and articles[edit | edit source]

BEXX,
ALDAX,
ALDAC,
AGGAX,
AGGAC,
AMGGAX,
AMGGAC,
LHFCALC,
HFSCREEN,
LMODELHF,
LTHOMAS,
LRHFCALC,
List of hybrid functionals,
Hybrid functionals: formalism

Examples that use this tag

References[edit | edit source]
