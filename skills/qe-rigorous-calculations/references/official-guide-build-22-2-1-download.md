# 2.1 Download

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node8.html
- Retrieved: 2026-07-17T11:50:45+00:00
- Official source SHA-256: `6f4dd489fc8777dd8618354783bc131b6d89d3a1e3383d02396ae446065508c8`
- Extracted text SHA-256: `fffb80de12f0e9971124e9a37ce7a7de9d8bc81698192c39905d1ddd3c582f96`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.2 Prerequisites for source compilation

Up:

2 Installation

Previous:

2 Installation

  

Contents

2.1 Download

Q
UANTUM 
ESPRESSO is distributed in source form, but selected binary packages,
virtual machines, dockers, may also be available.
Stable and development releases of the Q
UANTUM 
ESPRESSO source package
(current version is 7.5.0), as well as available binary
packages, can be downloaded from the links listed in the
``Download'' section of 
www.quantum-espresso.org
.

The Quantum Mobile virtual machine for Windows/Mac/Linux/Solaris
provides a complete Ubuntu Linux environment, containing Q
UANTUM 
ESPRESSO and
much more. Link and description in

https://www.materialscloud.org/work/quantum-mobile
.

For source compilation, uncompress and unpack compressed archives
in the typical .tar.gz format using the command:

tar zxvf qe-X.Y.Z.tar.gz

(a hyphen before "zxvf" is optional) where 
X.Y.Z
stands for the
version number.

A few additional packages that are not included in the base distribution
will be downloaded on demand at compile time, using either 
make
or

CMake
(see Sec.
2.7
).
Note however that this will work only if the computer you are
installing on is directly connected to the internet and has
either 
wget
or 
curl
installed and working.
If you run into trouble, manually download each required package
into subdirectory 
archive/
, 
not unpacking or
uncompressing it
:
command 
make
will take care of this during installation.

The Q
UANTUM 
ESPRESSO distribution contains several directories. Some of them are
common to all packages:

Modules/

Fortran modules and utilities used by all programs

upflib/

pseudopotential-related code, plus conversion tools

include/

files *.h included by fortran and C source files

FFTXlib/

FFT libraries

LAXlib/

Linear Algebra (parallel) libraries

KS_Solvers/

Iterative diagonalization routines

UtilXlib/

Miscellaneous timing, error handling, MPI utilites

XClib/

Exchange-correlation functionals (excepted van der Waals)

MBD/

Routines for many-body dispersions

dft-d3/

Routines for DFT-D3 disesive corrections

LR_Modules/

Fortran modules and utilities used by linear-response codes

install/

installation scripts and utilities

pseudo
/

pseudopotential files used by examples

Doc/

general documentation

external/

external libraries automatically downloaded

test-suite/

automated tests

while others are specific to a single package:

PW/

PWscf
package

EPW/

EPW
package

NEB/

PWneb
package

PP/

PostProc
package

PHonon/

PHonon
package

PWCOND/

PWcond
package

CPV/

CP
package

atomic/

atomic
package

GUI/

PWGui
package

HP/

HP
package

QEHeat/

QEHeat
package

KCW/

KCW
package

Finally, directory 
COUPLE/
contains code and documentation
that is useful to call Q
UANTUM 
ESPRESSO programs from external codes.

next 

up 

previous 

contents 

Next:

2.2 Prerequisites for source compilation

Up:

2 Installation

Previous:

2 Installation

  

Contents
```
