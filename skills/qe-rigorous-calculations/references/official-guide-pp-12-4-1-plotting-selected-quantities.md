# 4.1 Plotting selected quantities

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node6.html
- Retrieved: 2026-07-17T11:52:22+00:00
- Official source SHA-256: `9180846bacfb95a9666e0dcdd3fbfb9a474cf67f39d27b51632a1f46a5925053`
- Extracted text SHA-256: `c25d7a0f928e307386c90fdb95f90e2e9ba87e47fe18acd8763085b516b49029`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.2 About Bader's analysis

Up:

4 Usage

Previous:

4 Usage

  

Contents

Subsections

4.1.0.1 Planar averages

4.1.0.2 All-electron charge

4.1 Plotting selected quantities

The main postprocessing code 
pp.x
extracts the specified data
from the data files produced by 
PWscf
(
pw.x
executable) or 
CP

(
cp.x
executable); prepares data for plotting by writing them into 
formats that can be read by several plotting programs.

Quantities that can be read or calculated are:

charge density

spin polarization

various potentials

local density of states at 
E
F

local density of electronic entropy

STM images

selected squared wavefunction

ELF (electron localization function)

RDG (reduced density gradient)

integrated local density of states

Various types of plotting (along a line, on a plane, three-dimensional, polar)
and output formats (including the popular cube format) can be specified.
Moreover data can be saved to an intermediate (formatted) file so that
more data sets can be summed or subracted in a later run.
The output files can be directly read by the free plotting system Gnuplot
(1D or 2D plots), or by code 
plotrho.x
that comes with 
PostProc

and produces PostScript 2D plots,
or by advanced plotting software XCrySDen (3D plots).

See file 
PP/Doc/INPUT_PP.*
for a detailed description of the input
for code 
pp.x
.
See Example 01 for an example of a charge density plot, Example 03
for an example of STM image simulation.

4.1.0.1 Planar averages

Code 
plan_avg.x
calculates planar averages of Kohn-Sham orbitals.
Input documentation is in the header of
PP/src/plan_avg.f90
.

Code 
average.x
calculates planar averages of quantities produced
by 
pp.x
(e.g. potentials, charge, magnetization densities).
Note that 
average.x
reads the intermediate file produced
by 
pp.x
, not data files produced by 
pw.x
. Examples of usage 
of 
average.x
can be found in 
PP/examples/WorkFct_example/

and in 
PP/examples/dipole_example/
.

4.1.0.2 All-electron charge

pawplot.x
produces plots of the all-electron charge
for PAW calculations. Input documentation in the header of

PP/src/pawplot.f90
. 

next 

up 

previous 

contents 

Next:

4.2 About Bader's analysis

Up:

4 Usage

Previous:

4 Usage

  

Contents
```
