# ENAUG

- Official URL: https://www.vasp.at/wiki/ENAUG
- Page ID: 166
- Revision ID: 26953
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

ENAUG = [real]
Default: ENAUG = largest EAUG read from the POTCAR file

Description: Specifies the cutoff energy of the plane-wave representation of the augmentation charges in eV.

ENAUG determines NGXF, NGYF, and NGZF in accordance with the PREC tag.

Deprecated: ENAUG is considered as deprecated and should not be used anymore.

Warning: Setting ENAUG has an effect only if PREC is set to one of the old settings (Low, Medium or High), otherwise it is ignored.

Related tags and articles[edit | edit source]

NGXF,
NGYF,
NGZF,
ENCUT,
PREC,
PRECFOCK

Examples that use this tag
