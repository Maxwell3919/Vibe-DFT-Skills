# 2.7 Compilation

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node14.html
- Retrieved: 2026-07-17T11:50:21+00:00
- Official source SHA-256: `4031f39cf4e92ba7ff7dcc843c2c231372b1ba55b6e2cd156021df300bbd71ff`
- Extracted text SHA-256: `d116740a4b15cf108e8a3f98d70e9b6404a5f21412c657e01abb79ac15fab116`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.8 Running tests and examples

Up:

2 Installation

Previous:

2.6 Libxc library

  

Contents

2.7 Compilation

The compiled codes can run with any input: almost all variables are
dinamically allocated at run time. Only a few variables have fixed
dimensions, set in file 
Modules/parameters.f90
:

ntypx = 10, &! max number of different types of atom
npsx = ntypx, &! max number of different PPs (obsolete)
nsx = ntypx, &! max number of atomic species (CP)
npk = 40000, &! max number of k-points
lmaxx = 4, &! max non local angular momentum (l=0 to lmaxx)
lqmax= 2*lmaxx+1 ! max number of angular momenta of Q

These values should work for the vast majority of cases. In case you need
more atomic types or more k-points, edit this file and recompile.

At your choice, you may compile the complete Q
UANTUM 
ESPRESSO suite of programs
(with 
make all
), or only some specific programs.
All executables are linked in main 
bin
directory.

make
with no arguments yields ain updated list of valid compilation targets.

For the setup of the GUI, refer to the 
PWgui-X.Y.Z /INSTALL
file, where
X.Y.Z stands for the version number of the GUI (should be the same as the
general version number). If you are using sources from the git repository, see
the 
GUI/README
file instead.

If 
make
refuses for some reason to download additional
packages, manually download them into subdirectory

archive/
, 
not
unpacking or uncompressing them,
and try 
make
again. Also see Sec.(
2.1
).
```
