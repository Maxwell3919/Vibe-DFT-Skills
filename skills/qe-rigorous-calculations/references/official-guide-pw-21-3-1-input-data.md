# 3.1 Input data

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node8.html
- Retrieved: 2026-07-17T11:51:28+00:00
- Official source SHA-256: `a7b92a49b2aaa91b09a982f942a5194f2105b2562ee96b1c480d9f1c048ca242`
- Extracted text SHA-256: `012c6ca695231ee7cb89392979622a225c8453d020bac5608668fad42ccb003d`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.2 Data files

Up:

3 Using PWscf

Previous:

3 Using PWscf

  

Contents

3.1 Input data

Input data 
is organized as several namelists, followed by other fields (``cards'')
introduced by keywords. The namelists are

&CONTROL:

general variables controlling the run

&SYSTEM:

structural information on the system under investigation

&ELECTRONS:

electronic variables: self-consistency, smearing

&IONS (optional):

ionic variables: relaxation, dynamics

&CELL (optional):

variable-cell optimization or dynamics

Optional namelist may be omitted if the calculation to be performed
does not require them. This depends on the value of variable 

calculation

in namelist &CONTROL. Most variables in namelists have default values. Only
the following variables in &SYSTEM must always be specified:

nat

(integer)

number of atoms in the unit cell

ntyp

(integer)

number of types of atoms in the unit cell

ecutwfc

(real)

kinetic energy cutoff (Ry) for wavefunctions.

plus the variables needed to describe the crystal structure, e.g.:

ibrav

(integer)

Bravais-lattice index

celldm

(real, dimension 6)

crystallographic constants

Alternative ways to input structural data are described in files

PW/Doc/INPUT_PW.*
. For metallic systems, you have to specify
how metallicity is treated in variable 
occupations
.
If you choose 
occupations='smearing'
, you have
to specify the smearing type 
smearing
and the smearing width 

degauss
. Spin-polarized systems are as a rule treated as metallic 
system, unless the total magnetization, 
tot_magnetization

is set to a fixed value, or if occupation numbers are fixed
(
occupations='from input'
and card OCCUPATIONS).

Detailed explanations of the meaning of all variables are found in files

PW/Doc/INPUT_PW.*
. Almost all variables have default 
values, which may or may not fit your needs.

Comment lines in namelists can be introduced by a "!", exactly as in fortran 
code. 

After the namelists, you have several fields (``cards'')
introduced by keywords with self-explanatory names:

ATOMIC_SPECIES

ATOMIC_POSITIONS

K_POINTS

CELL_PARAMETERS (optional)

OCCUPATIONS (optional)

The keywords may be followed on the same line by an option. Unknown
fields are ignored. 
See the files mentioned above for details on the available ``cards''.

Comments lines in ``cards'' can be introduced by either a ``!'' or a ``#''
character in the first position of a line.

Note about k-points: The k-point grid can be either automatically generated 
or manually provided as a list of k-points and a weight in the Irreducible
Brillouin Zone only of the Bravais lattice of the crystal. The code will 
generate (unless instructed not to do so: see variable 
nosym
) all
required k-points
and weights if the symmetry of the system is lower than the symmetry of the
Bravais lattice. The automatic generation of k-points follows the convention
of Monkhorst and Pack.

next 

up 

previous 

contents 

Next:

3.2 Data files

Up:

3 Using PWscf

Previous:

3 Using PWscf

  

Contents
```
