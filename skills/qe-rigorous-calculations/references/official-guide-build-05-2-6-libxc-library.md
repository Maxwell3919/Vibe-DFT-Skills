# 2.6 Libxc library

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node13.html
- Retrieved: 2026-07-17T11:50:20+00:00
- Official source SHA-256: `41460e50e88292652b7abdb14743ea2e7c5ae340406beb3f7f0374d2f2935e7b`
- Extracted text SHA-256: `cf7b47714dec098f7e03dfabdbab19517a96dac5f1f9ff7f3fa405563508bbc3`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.7 Compilation

Up:

2 Installation

Previous:

2.5 Libraries

  

Contents

Subsections

2.6.1 Linking in Q
UANTUM 
ESPRESSO

2.6.1.1 With CMake:

2.6.1.2 Note for versions newer than 5.0.0:

2.6.2 Usage

2.6.3 Differences between Libxc and internal functionals

2.6.4 Special cases

2.6.4.1 External parameters.

2.6.4.2 Functionals with partial output.

2.6.4.3 MGGA Functionals that depend on the Laplacian of the density.

2.6.4.4 Other functionals.

2.6.5 XC test

2.6 Libxc library

Q
UANTUM 
ESPRESSO is compatible with 
libxc
version 4.3.0 or later (compatibility with older versions is not guaranteed).

The 
libxc
functionals are available for LDA, GGA and metaGGA, however, not all of them are straightforwardly usable. Some of them may depend on specific external parameters and some others may provide as output the energy or the potential, but not both. Therefore some attention has to be paid when using 
libxc
. Warning messages should appear in the output when particular cases whose correct operation in Q
UANTUM 
ESPRESSO is not guaranteed are chosen.

2.6.1 Linking in Q
UANTUM 
ESPRESSO

Once installed 
libxc
, the linking with Q
UANTUM 
ESPRESSO can be enabled directly through the configuration script by adding the two switches 
–with-libxc
and 
–with-libxc-prefix
, e.g.:

./configure --with-libxc --with-libxc-prefix='/path/to/libxc/'

By adding the first switch only an automatic search for the 
libxc
folder will be attempted, but its success is not guaranteed. It is always preferable to specify the second switch too. Optionally, a third switch can be added, namely 
–with-libxc-include='/path/to/libxc/include'
, which specifies the path to the Fortran headers (usually it is not necessary).

Alternatively, the link to 
libxc
can be activated after the configuration of Q
UANTUM 
ESPRESSO by modifying the 
make.inc
file in the main folder in this way:

add 
-D__LIBXC
to 
DFLAGS

add 
-I/path/to/libxc/include/
to 
IFLAGS

set 
LD_LIBS=-L/path/to/libxc/lib/ -lxcf03 -lxc

Then Q
UANTUM 
ESPRESSO can be compiled as usual.

Note: if the version of 
libxc
is 5.0.0, the last point must be replaced by:

set 
LD_LIBS=-L/path/to/libxc/lib/ -lxcf90 -lxc

since the 
f03
interfaces are no longer available. They have been restored in following releases. Version 5.0.0 is still usable, but, before compiling Q
UANTUM 
ESPRESSO, a string replacement is necessary, namely `
xc_f03
' must be replaced with `
xc_f90
' everywhere in the 
XClib
folder.

2.6.1.1 With CMake:

when executing 
cmake
in the build folder, add the following flags:

cmake [....] -DQE_ENABLE_LIBXC=ON -DLIBXC_INCLUDE_DIR=path/to/libxc/include ..

If 
cmake
is not able to find the package you may need to do this: in Q
UANTUM 
ESPRESSO main folder open 
CMakeLists.txt
and, inside the block 
if(QE\_ENABLE\_LIBXC)
, near line 583, add this:

set(ENV{PKG_CONFIG_PATH} "$ENV{PKG\_CONFIG\_PATH}:/path/to/libxc/pkgconfig")

then execute 
cmake
as above and compile.

2.6.1.2 Note for versions newer than 5.0.0:

libxc
enforces the Fermi hole curvature by default, which might lead to inexact results and convergence problems when using some MGGA functionals in Q
UANTUM 
ESPRESSO. This should be switched off by adding the 
--disable-fhc
flag when compiling 
libxc
.

2.6.2 Usage

In order to use 
libxc
functionals, you can enforce them from input by including the 
input_dft
string in the 
system
namelist. Starting from v7.0 of Q
UANTUM 
ESPRESSO the only allowed notation for DFTs that include Libxc terms is the index one. For example, to use the 
libxc
version of the PBE functional (both exchange and correlation):

input_dft = `XC-000I-000I-101L-130L-000I-000I'

The letters I or L next to each ID stand for Internal and 
libxc
. This is equivalent to the old full-name notation:

input_dft = `gga_x_pbe gga_c_pbe' ***OLD***

The order must be the usual one, namely LDA exchange, LDA correlation, GGA exchange, GGA correlation, MGGA exchange, MGGA correlation. 
libxc
exchange+correlation functionals can be put in the exchange or in the correlation slot with no difference.

The reason why the full-name notation has been disabled is to eliminate the risk of overlaps among different names (occurring especially when combinations of internal and 
libxc
DFTs are used).

The complete list of 
libxc
functionals and IDs is available at:

https://libxc.gitlab.io/
.
Combinations of Q
UANTUM 
ESPRESSO and 
libxc
functionals are allowed in 
PW
, but some attention has to be paid to their reciprocal compatibility (see section below).

For example, the internal exchange term of PBE together with the correlation term of PBE in 
libxc
is obtained by:

input_dft = `XC-001I-000I-003I-130L-000I-000I'

which corresponds to the old:

input_dft = `sla pbx gga_c_pbe' ***OLD***

Note that when using GGA internal functionals you must always specify the LDA term too, while it is not the case for the 
libxc
ones.

Abbreviations are allowed when zero tails are present. The above example is still valid by putting:

input_dft = `XC-001I-000I-003L-130L'

since no MGGA terms are present.

Non-local terms can be included by just adding their name after the index notation, for example:

input_dft=`XC-001i-004i-013i-vdw2'

2.6.3 Differences between Libxc and internal functionals

There are some differences between Q
UANTUM 
ESPRESSO functionals and 
libxc
ones. In Q
UANTUM 
ESPRESSO the LDA and the GGA terms are separated and must be specified independently. In 
libxc
the GGA functionals already include the LDA part (Slater exchange and Perdew&Wang correlation in most of the cases with the exception, for example, of Lee Yang Parr functionals).

The 
libxc
metaGGA functionals may or may not need the LDA and GGA terms, depending on the cases, therefore a good check of the chosen functionals is recommended before doing expensive runs.

Some functionals in 
libxc
incorporate the exchange part and the correlation one into one term only (e.g. the ones that include the `
_xc
' kind label in their name). In these cases the whole functional is formally treated as `correlation only' by Q
UANTUM 
ESPRESSO. This does not imply any loss of information.

2.6.4 Special cases

A number of 
libxc
functional routines need extra information on input and/or provide only partial information on output (e.g. the energy or the potential only). In these cases the use of such functionals may not be straightforward and, depending on the cases, may require some work on the Q
UANTUM 
ESPRESSO source code.

2.6.4.1 External parameters.

Several functionals in 
libxc
depend on one or more external parameters. Some of these can be recovered inside Q
UANTUM 
ESPRESSO, some others are not directly available. In all these cases a direct intervention on the Q
UANTUM 
ESPRESSO source code might be necessary in order to be able to properly use such functionals. However two routines have been defined in the XC library of Q
UANTUM 
ESPRESSO that ease the task of setting and recovering the external parameters in 
libxc
:

get_libxc_ext_param
: this function receives as input the ID of the 
libxc
functional and the index of the chosen parameter and returns its value. If the parameter has not been set before it returns its default value.

set_libxc_ext_param
: this routine receives as input the index of the functional family-type (from 1 to 6: lda-exch, lda-corr, gga-exch, ...), the index of the chosen 
libxc
parameter and the value to set it to.

In order to see the available parameters for a given 
libxc
functional and their corresponding indexes, the 
xc_infos.x
program is available in 
XClib
folder. For more details see Sec. 
2.6.5
.

The two routines can be called almost anywhere in Q
UANTUM 
ESPRESSO, however, as any other 
XClib
setting routine, they must be declared through the 
xc_lib
module.

Without setting the external parameters inside the code, their default value will be assumed. This could lead to results different from the expectations.

In any case, when external parameters are needed by the chosen functionals, a warning message will appear in the output of Q
UANTUM 
ESPRESSO. An example of Libxc parameter setting can be found in the 
xclib_test.f90
code (see below).

2.6.4.2 Functionals with partial output.

A few 
libxc
functional routines provides the potential but not the energy. These functionals are available in Q
UANTUM 
ESPRESSO for all the families and their output energy is set to zero.

2.6.4.3 MGGA Functionals that depend on the Laplacian of the density.

At present such functionals are formally usable in Q
UANTUM 
ESPRESSO , but their dependency on the Laplacian is ignored and the corresponding output term of the potential is set to zero. Since the Laplacian of the density is computable in Q
UANTUM 
ESPRESSO, they might be fully exploited with a limited intervention on the code.

2.6.4.4 Other functionals.

Besides exchange (
_x
), correlation (
_c
) and exchange plus correlation (
_xc
), a fourth kind of functionals is available in 
libxc
, the kinetic functionals (
_k
). At present, they are not usable in Q
UANTUM 
ESPRESSO.

2.6.5 XC test

A testing program, 
xclib_test.x
, for the 
XClib
library of Q
UANTUM 
ESPRESSO is available. The program is available for LDA, GGA and MGGA functionals (both QE and Libxc). It also tests the potential derivatives for LDA (
dmxc
) and GGA (
dgcxc
).

Another small program, 
xc_infos.x
, is available in the 
XClib
folder starting from v6.8. It receives as input the name of any DFT usable in Q
UANTUM 
ESPRESSO (both internal and 
libxc
) and provides infos about their family, type, external parameters, limitations, references, etc.

See XClib/README.TEST file for further details on each of the two programs.

next 

up 

previous 

contents 

Next:

2.7 Compilation

Up:

2 Installation

Previous:

2.5 Libraries

  

Contents
```
