# 3 Compilation

- Official source: https://www.quantum-espresso.org/Doc/neb_user_guide/node4.html
- Retrieved: 2026-07-17T11:52:39+00:00
- Official source SHA-256: `afaab78a3cf93c1ed98c28d6bd2e5bb4c1874599a867fb8cdf4fd027e2594212`
- Extracted text SHA-256: `c7550b000048d9fe2b947b35f17e980c1cc42fbf304630e4ea7418971c12fe5b`
- Official Last-Modified: Mon, 08 Dec 2025 20:53:13 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.1 Running examples

Up:

User's Guide for The Quantum

Previous:

2 People and terms of

  

Contents

3 Compilation

PWneb
is a package of Q
UANTUM 
ESPRESSO and requires package 
PWscf
for
compilation.
For instruction on how to download and compile Q
UANTUM 
ESPRESSO, please refer 
to the general Users' Guide, available in file 
Doc/user_guide.pdf

under the main Q
UANTUM 
ESPRESSO directory, or in web site 

http://www.quantum-espresso.org
.

Once Q
UANTUM 
ESPRESSO is correctly configured, 
PWneb
can be automatically 
downloaded, unpacked and compiled by
just typing 
make neb
, from the main Q
UANTUM 
ESPRESSO directory.

make neb
will produce 
the following codes in 
NEB/src
:

neb.x
: calculates reaction barriers and pathways using NEB.

path_interpolation.x
: generates a reaction path (a set of points
in the configuration space of the atomic system, called ``images''), by
interpolating the supplied path. The new path can have a 
different number of images than the old one and the initial and final 
images of the new path can differ from the original ones.
The utility 
path_interpolation.sh
in the 
tools/

directory shows how to use the code.

Symlinks to executable programs will be placed in the

bin/
subdirectory of the main Q
UANTUM 
ESPRESSO directory.

Subsections

3.1 Running examples
```
