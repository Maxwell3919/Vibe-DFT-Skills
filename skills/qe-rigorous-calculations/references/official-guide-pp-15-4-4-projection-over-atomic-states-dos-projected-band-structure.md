# 4.4 Projection over atomic states, DOS, projected band structure

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node9.html
- Retrieved: 2026-07-17T11:52:27+00:00
- Official source SHA-256: `5e114fbc14d234422f093269a1084d0f3fa74256feeeec531cb7c3144fcabe67`
- Extracted text SHA-256: `77e62675a65870e5c92dbb5af4dd64d8960f0d5417840f59dc2aee0a958bcce4`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.5 Color plot of the

Up:

4 Usage

Previous:

4.3 Band structure, Fermi surface

  

Contents

4.4 Projection over atomic states, DOS, projected band structure

The code 
projwfc.x
calculates projections of wavefunctions
over atomic orbitals. The atomic wavefunctions are those contained
in the pseudopotential file(s). The Löwdin population analysis (similar to
Mulliken analysis) is presently implemented. The projected DOS (or PDOS:
the DOS projected onto atomic orbitals) can also be calculated and written
to file(s). More details on the input data are found in file

PP/Doc/INPUT_PROJWFC.*
. The ordering of the various 
angular momentum components (defined in routine 
ylmr2.f90
)
is as follows:

P
0, 0
(
t
), 

P
1, 0
(
t
), 

P
1, 1
(
t
)
cosφ
, 

P
1, 1
(
t
)
sinφ
,

P
2, 0
(
t
), 

P
2, 1
(
t
)
cosφ
, 

P
2, 1
(
t
)
sinφ
, 

P
2, 2
(
t
)
cos
2
φ
, 

P
2, 2
(
t
)
sin
2
φ

and so on, where 
P
l, m
=Legendre Polynomials, 

t
= 
cosθ
= 
z
/
r
, 

φ
= 
atan
(
y
/
x
).

Data produced by code 
projwfc.x
can be further 
analysed using auxiliary codes 
sumpdos.x
(sums selected PDOS
by specifying the names of files containing the desired PDOS: type 

sumpdos.x -h
or look into the source code for more details) 
and 
plotproj.x
. A more sophisticated tools is the script

PP/tools/sum_states.py
, by Julen Larrucea: documentation in

http://larrucea.eu/sum_states-py-2/
.

The total electronic DOS can also be calculated by code 
dos.x
,
whose complete input documentation is in 
PP/Doc/INPUT_DOS.*

See Example 02 for total and projected electronic DOS calculations,
-and for projected band structure;
see Example 03 for projected and local DOS calculations.

The DOS projected over 
molecular
states (e.g. for a molecule on
a surface system) can be computed using code 
molecularpdos.x

(courtesy of Guido Fratesi). See file 
PP/Doc/INPUT_MOLDOS.*

for input documentation and directory 
PP/examples/MolDos_example/
for
an example.

The calculation of magnetic anisotropy using the Force Theorem is described
in the following paper:
https://journals.aps.org/prb/abstract/10.1103/PhysRevB.90.205409. An
example and a README can be found in 
PP/examples/ForceTheorem_example/

next 

up 

previous 

contents 

Next:

4.5 Color plot of the

Up:

4 Usage

Previous:

4.3 Band structure, Fermi surface

  

Contents
```
