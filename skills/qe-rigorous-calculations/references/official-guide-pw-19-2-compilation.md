# 2 Compilation

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node6.html
- Retrieved: 2026-07-17T11:51:23+00:00
- Official source SHA-256: `ddf494ac2a40662ccd1ef8bee35d535308868c14423df7d783f9e273d32fc209`
- Extracted text SHA-256: `1828a125ad1872a1c12128d1a16788259020365197390ad0314b34ff3d44e1d7`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3 Using PWscf

Up:

User's Guide for the PWscf

Previous:

1.3 Terms of use

  

Contents

2 Compilation

PWscf
is included in the core Q
UANTUM 
ESPRESSO distribution.
Instruction on how to install it can be found in the
general documentation (User's Guide) for Q
UANTUM 
ESPRESSO.

Typing 
make pw
from the main Q
UANTUM 
ESPRESSO directory or

make
from the 
PW/
subdirectory produces
the 
pw.x
executable in 
PW/src
and a link to the

bin/
directory. In addition, the following utility
programs, and related links in 
bin/
, are produced
in 
PW/src
:

dist.x
symbolic link to 
pw.x
: reads input data for 
PWscf
,
calculates distances and angles between atoms in a cell,
taking into account periodicity,

and in 
PW/tools
:

ev.x
fits energy-vs-volume data to an equation of state

kpoints.x
produces lists of k-points

ibrav2cell.x
and 
cell2ibrav.x
convert from
variables used in Q
UANTUM 
ESPRESSO to specify the unit cell to primitive
lattice translations, and vice versa 

scan_ibrav.x
works as 
cell2ibrav.x
but tries
to figure out whether the axis are rotated with respect to those
assumed by Q
UANTUM 
ESPRESSO

pwi2xsf.sh
, 
pwo2xsf.sh
process respectively 
input and output files (not data files!) for 
pw.x
and 
neb.x

(the latter, courtesy of Pietro Bonfà) and produce an XSF-formatted file
suitable for plotting with XCrySDen:

http://www.xcrysden.org/
, a powerful crystalline and
molecular structure visualization program.
BEWARE: the 
pwi2xsf.sh
shell script requires the

pwi2xsf.x
executables to be located somewhere in your PATH. 

cif2qe.sh
: script converting from CIF 
(Crystallographic Information File) to a format suitable for Q
UANTUM 
ESPRESSO.
Courtesy of Carlo Nervi (Univ. Torino, Italy).

The other auxiliary codes contain their own documentation in the source
files.

next 

up 

previous 

contents 

Next:

3 Using PWscf

Up:

User's Guide for the PWscf

Previous:

1.3 Terms of use

  

Contents
```
