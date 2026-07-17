# SYMPREC

- Official URL: https://www.vasp.at/wiki/SYMPREC
- Page ID: 298
- Revision ID: 27002
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

SYMPREC = [real]
Default: SYMPREC = [math]\displaystyle{ 10^{-5} }[/math]

Description: SYMPREC determines to which accuracy the positions in the POSCAR file must be specified (as of VASP.4.4.4).

SYMPREC determines how accurately the positions in the POSCAR file must be specified.
The default, SYMPREC=10-5, is usually large enough, even if the POSCAR file has been generated with single precision accuracy.
Increasing SYMPREC means that the positions in the POSCAR file can be specified with less accuracy (increasing fuzziness). Please also have a look at this section.

Related tags and articles[edit | edit source]

ISYM

Examples that use this tag
