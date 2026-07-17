# INPUT_NEB — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `0928d0278a3e5b877ccef652eb2f8a7858651cc2763d064aa5c2df2baef1515a`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: neb.x / NEB / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, | = or

All quantities whose dimensions are not explicitly specified are in
RYDBERG ATOMIC UNITS

BEWARE: TABS, DOS <CR><LF> CHARACTERS ARE POTENTIAL SOURCES OF TROUBLE

neb.x DOES NOT READ FROM STANDARD INPUT !

There are two ways for running a calculation with neb.x:

(1) specifying a file to parse with the ./neb.x -inp or ./neb.x -input
    command line option.

(2) or specifying the number of copies of PWscf inputs with the ./neb.x -input_images

For case (1) a file containing special KEYWORDS (aka SUPERCARDS) has to be
written (see below). These KEYWORDS tell the parser which part of the file
contains the neb specifics and which part contains the energy/force engine
input (at the moment only PW).  After the parsing, different files are
generated: neb.dat, with the neb specific variables, and a set of pw_*.in
PWscf input files, i.e., one for each input position. All options for a
single SCF calculation apply.

The general structure of the file to be parsed is:
==================================================

BEGIN
  BEGIN_PATH_INPUT
    ... neb specific namelists and cards
  END_PATH_INPUT

  BEGIN_ENGINE_INPUT
    ...pw specific namelists and cards
    BEGIN_POSITIONS
      FIRST_IMAGE
      ...pw ATOMIC_POSITIONS card
      ...pw TOTAL_CHARGE card (only for FCP)
      INTERMEDIATE_IMAGE
      ...pw ATOMIC_POSITIONS card
      ...pw TOTAL_CHARGE card (only for FCP)
      LAST_IMAGE
      ...pw ATOMIC_POSITIONS card
      ...pw TOTAL_CHARGE card (only for FCP)
    END_POSITIONS
    ... other pw specific cards
  END_ENGINE_INPUT
END


For case (2) neb.dat and all pw_1.in, pw_2.in ... should be already present.

Structure of the NEB-only input data (file neb.dat):
====================================================

&PATH
  ...
/

[ CLIMBING_IMAGES
   list of images, separated by a comma ]



########################################################################
| SUPERCARD: BEGIN/END
| this supercard is enclosed within the keywords:
|
| BEGIN
|    ... content of the supercard here ...
| END
|
| The syntax of supercard's content follows below:

   ########################################################################
   | SUPERCARD: BEGIN_PATH_INPUT/END_PATH_INPUT
   | this supercard is enclosed within the keywords:
   |
   | BEGIN_PATH_INPUT
   |    ... content of the supercard here ...
   | END_PATH_INPUT
   |
   | The syntax of supercard's content follows below:
   
      ========================================================================
```
