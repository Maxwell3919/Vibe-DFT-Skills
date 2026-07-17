# INPUT_PP — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `d8f690d2c76b6028238ad25761e636266cb65c041811fa331336badc6194b888`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
Input File Description 

Program:
pp.x / PWscf / Quantum ESPRESSO
(version: 7.5)

TABLE OF CONTENTS

INTRODUCTION

&INPUTPP

title
| 
prefix
| 
outdir
| 
filplot
| 
plot_num
| 
spin_component
| 
spin_component
| 
emin
| 
emax
| 
delta_e
| 
degauss_ldos
| 
use_gauss_ldos
| 
sample_bias
| 
kpoint
| 
kband
| 
lsign
| 
spin_component
| 
emin
| 
emax
| 
spin_component
| 
spin_component
| 
spin_component
| 
spin_component
| 
nc
| 
n0

&PLOT

nfile
| 
filepp
| 
weight
| 
iflag
| 
output_format
| 
fileout
| 
interpolation
| 
e1
| 
x0
| 
nx
| 
e1
| 
e2
| 
x0
| 
nx
| 
ny
| 
e1
| 
e2
| 
e3
| 
x0
| 
nx
| 
ny
| 
nz
| 
radius
| 
nx
| 
ny

INTRODUCTION

Purpose of pp.x:
data analysis and plotting.

The code performs two steps:

(1) reads the output produced by 
pw.x,
extracts and calculates
the desired quantity/quantities (rho, V, ...)

(2) writes the desired quantity to file in a suitable format for
various types of plotting and various plotting programs

The input data of this program is read from standard input
or from file and has the following format:

NAMELIST 
&INPUTPP

containing the variables for step (1), followed by

NAMELIST 
&PLOT

containing the variables for step (2)

The two steps can be performed independently. In order to perform
only step (2), leave namelist 
&INPUTPP
blank. In order to perform
only step (1), do not specify namelist 
&PLOT

Intermediate results from step 1 can be saved to disk (see
variable 
filplot
in 
&INPUTPP)
and later read in step 2.
Since the file with intermediate results is formatted, it
can be safely transferred to a different machine. This
also allows plotting of a linear combination (for instance,
charge differences) by saving two intermediate files and
combining them (see variables 
weight
and 
filepp
in 
&PLOT)

All output quantities are in ATOMIC (RYDBERG) UNITS unless
otherwise explicitly specified.
All charge densities integrate to the NUMBER of electrons
not to the total charge.
All potentials have the dimension of an energy (e*V, not V).
```
