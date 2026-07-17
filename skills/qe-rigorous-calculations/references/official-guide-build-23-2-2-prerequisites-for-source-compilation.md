# 2.2 Prerequisites for source compilation

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node9.html
- Retrieved: 2026-07-17T11:50:47+00:00
- Official source SHA-256: `9d1bd7ba19ac077b983dd647d3915b3593a033d439f1bce64d1e955244101f99`
- Extracted text SHA-256: `28413def1e4b3c99f9742b56f03363771d75762e9163c33f5056a6ec848447bd`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.3 Building with CMake

Up:

2 Installation

Previous:

2.1 Download

  

Contents

2.2 Prerequisites for source compilation

First of all, you need a minimal Unix environment: a command shell 
like bash or sh, utilities 
make
, 
awk
, 
sed
. 
Note that the scripts contained in the distribution 
assume that the local language is set to the standard, i.e. "C"; 
other settings may break them. Use 
export LC_ALL=C
(sh/bash) 
or 
setenv LC_ALL C
(csh/tcsh) to prevent any problem
when running those scripts.

If you are not compiling a stable release from tarballs,
you will also need 
git
v.2.13 or later to get the 
external libraries.
You will need either CMake v.3.20 or later, or the 
configure

command from 
autoconf
v. 2.64 or later.

Second, you need a Fortran compiler compliant with F2008 standard
and any half-decent C compiler.
For parallel execution, a parallel MPI-aware Fortran compiler 
and MPI libraries implementing v.3 of the standard (notably, 
non-blocking broadcast and gather operations) are required.
For massively parallel machines, or for simple multicore parallelization, 
an OpenMP-aware Fortran compiler and libraries are also required. 
To compile 
for NVidia GPUs you need the NVidia HPC SDK (software development kit) 
v.21.7 or later, freely available for download.

As a rule, Q
UANTUM 
ESPRESSO tries to keep compatibility with older compilers,
avoiding nonstandard extensions and newer features that are not
widespread or stabilized. If however your compiler is older than
a few (∼5) years, it is likely that something will not work.
The same applies to mathematical and MPI libraries.

Big computing centers typically provide a Fortran compiler complete
with all needed libraries. Workstations or ``commodity'' machines
using PC hardware, may or may not have the needed software. If not,
you may use the open-source gfortran compiler from the gcc distribution,
and possibly open-source MPI libraries and run-time software. You may 
also get a commercial compiler, some of which are available free of charge 
under some conditions (e.g. academic or personal usage, no support) and may 
provide MPI libraries and run-time software as well.

next 

up 

previous 

contents 

Next:

2.3 Building with CMake

Up:

2 Installation

Previous:

2.1 Download

  

Contents
```
