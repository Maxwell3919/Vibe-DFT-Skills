# 3.3 Electronic structure calculations

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node10.html
- Retrieved: 2026-07-17T11:50:54+00:00
- Official source SHA-256: `5f381f3162a08df216e9da26304195914fabeca9b9a65a45359fa5828f09fca4`
- Extracted text SHA-256: `bd4adb08cd7d51f4358298960152cdcfade65d3a72e334b2a987ae169fc7f025`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.4 Optimization and dynamics

Up:

3 Using PWscf

Previous:

3.2 Data files

  

Contents

Subsections

3.3.0.1 Single-point (fixed-ion) SCF calculation

3.3.0.2 Band structure calculation

3.3.0.3 Noncollinear magnetization, spin-orbit interactions

3.3.0.4 DFT+U

3.3.0.5 Dispersion Interactions (DFT-D)

3.3.0.6 Hartree-Fock and Hybrid functionals

3.3.0.7 Dispersion interaction with non-local functional (vdW-DF)

3.3.0.8 Polarization via Berry Phase

3.3.0.9 Finite electric fields

3.3.0.10 Orbital magnetization

3.3 Electronic structure calculations

3.3.0.1 Single-point (fixed-ion) SCF calculation

Set 
calculation='scf'
(this is actually the default).
Namelists &IONS and &CELL will be ignored. For LSDA spin-polarized 
calculations (that is: with a fixed quantization axis for magnetization),
set 
nspin=2
. Note that the number of k-points will be internally
doubled (one set of k-points for spin-up, one set for spin-down).
See example 1 (that is: 
PW/examples/example01
).

3.3.0.2 Band structure calculation

First perform a SCF calculation as above;
then do a non-SCF calculation (at fixed potential, computed in the
previous step) with the desired k-point grid and number 
nbnd

of bands. 
Use 
calculation='bands'
if you are interested in calculating
only the Kohn-Sham states for the given set of k-points
(e.g. along symmetry lines: see for instance

http://www.cryst.ehu.es/cryst/get_kvec.html
). Specify instead

calculation='nscf'
if you are interested in further processing 
of the results of non-SCF calculations (for instance, in DOS calculations).
In the latter case, you should specify a uniform grid of points.
For DOS calculations you should choose 
occupations='tetrahedra'
, 
together with an automatically generated uniform k-point grid 
(card K_POINTS with option ``automatic'').
Specify 
nosym=.true.
to avoid generation of additional k-points in
low-symmetry cases. Variables 
prefix
and 
outdir
, which
determine
the names of input or output files, should be the same in the two runs.
See examples 1, 6, 7.

NOTA BENE: in non-scf calculations, the atomic positions are read by
default from the data file of the scf step, not from input.

3.3.0.3 Noncollinear magnetization, spin-orbit interactions

The following input variables are relevant for noncollinear and
spin-orbit calculations: 

noncolin

lspinorb

starting_magnetization
(one for each type of atoms)

To make a spin-orbit calculation both 
noncolin
and

lspinorb
must be true. Furthermore you must use fully
relativistic pseudopotentials at least for one atom. If all
pseudopotentials are scalar-relativistic, the calculation is
noncollinear but there is no spin-orbit coupling.

If 
starting_magnetization
is set to zero (or not given) 
the code makes a spin-orbit calculation without spin magnetization 
(it assumes that time reversal symmetry holds and it does not calculate 
the magnetization). The states are still two-component spinors but the
total magnetization is zero. 

If 
starting_magnetization
is different from zero, the code makes a 
noncollinear spin polarized calculation with spin-orbit interaction. The 
final spin magnetization might be zero or different from zero depending 
on the system. Note that the code will look only for symmetries that leave
the starting magnetization unchanged.

See example 6 for noncollinear magnetism, example 7 (and references
quoted therein) for spin-orbit interactions.

3.3.0.4 DFT+U

DFT+U (formerly known as LDA+U) calculation can be
performed within a simplified rotationally invariant form 
of the 
U
Hubbard correction. Note that for all atoms having 
a 
U
value there should be an item in function

Modules/set_hubbard_l.f90
and one in 
subroutine 
PW/src/tabd.f90
, defining respectively
the angular momentum and the occupancy of the orbitals with
the Hubbard correction. If your Hubbard-corrected atoms are not
there, you need to edit these files and to recompile.

See example 8 and its README.

3.3.0.5 Dispersion Interactions (DFT-D)

For DFT-D (DFT + semiempirical dispersion interactions), see the
description of input variable 
vdw_corr
and related
input variables; sample input files can be found in

test-suite/pw_vdw/vdw-d*.in
. For DFT-D2, see also the
comments in source file 
Modules/mm_dispersion.f90
.
For DFT-D3, see the README in the 
dft-d3/
directory.

3.3.0.6 Hartree-Fock and Hybrid functionals

Hybrid functionals do not require anything special to be done,
but note that: 1) they are much slower than plain GGA calculations,
2) non-scf and band calculations are not presently implemented, and
3) there are no pseudopotentials generated for hybrid functionals.
See 
EXX_example/
and its README file, and tests

pw_b3lyp
, 
pw_pbe
, 
pw_hse
.

3.3.0.7 Dispersion interaction with non-local functional (vdW-DF)

See example 
vdwDF_example
, references quoted in file

README
therein, tests 
pw_vdW
.

3.3.0.8 Polarization via Berry Phase

See example 4, its file README, the documentation in the header of 

PW/src/bp_c_phase.f90
. 

3.3.0.9 Finite electric fields

There are two different implementations of macroscopic electric fields
in 
pw.x
: via an external sawtooth potential (input variable

tefield=.true.
) and via the modern theory of polarizability
(
lelfield=.true.
).
The former is useful for surfaces, especially in conjunction
with dipolar corrections (
dipfield=.true.
):
see the web page – courtesy Christoph Wolf –

https://christoph-wolf.at/tag/dipfield
, and 

PP/examples/dipole_example
for an example of application. 
Electric fields via modern theory of polarization are documented in
example 10. The exact meaning of the related variables, for both
cases, is explained in the general input documentation.

3.3.0.10 Orbital magnetization

Modern theory of orbital magnetization [Phys. Rev. Lett. 95, 137205 (2005)]
for insulators. The calculation is performed by setting 
input variable 
lorbm=.true.
in nscf run. If finite electric field 
is present (
lelfield=.true.
) only Kubo terms are computed
[see New J. Phys. 12, 053032 (2010) for details].

next 

up 

previous 

contents 

Next:

3.4 Optimization and dynamics

Up:

3 Using PWscf

Previous:

3.2 Data files

  

Contents
```
