# 4.8 Other tools

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node13.html
- Retrieved: 2026-07-17T11:52:13+00:00
- Official source SHA-256: `a1ef628a7e02f9c0928e3e2c9606884db38e7a755736e0e61b7b90541012680c`
- Extracted text SHA-256: `1df4c3cf38f56c0787cde4f413c093af27283a79dce613945c1a8e83d98aa6bb`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

5 Troubleshooting

Up:

4 Usage

Previous:

4.7 Interfaces to/from other code

  

Contents

Subsections

4.8.0.1 Exchange-correlation

4.8.0.2 Wavefunction conversion

4.8.0.3 Dielectric function

4.8.0.4 Core-level shifts

4.8 Other tools

4.8.0.1 Exchange-correlation

Code 
ppacf.x
computes the coupling constant dependency of the
exchange correlation potential 

E
xc, 
λ
, 
λ
∈[0 : 1]
and the spatial distribution of the exchange-correlation energy density
and kinetic correlation energy density according to:
Y. Jiao, E. Schröder, and P. Hyldgaard, Phys. Rev. B 97, 085115 (2018).
See 
PP/Doc/INPUT_PPACF.html
.

4.8.0.2 Wavefunction conversion

Code 
wfck2r.x
converts Kohn-Sham orbitals from reciprocal to real 
space. It is a useful starting point if you need to access wavefunctions
and perform postprocessing operations that are not implemented in Q
UANTUM 
ESPRESSO.

4.8.0.3 Dielectric function

Code 
epsilon.x
calculates RPA frequency-dependent complex dielectric 
function. Documentation is in file 
Doc/eps_man.tex
.

4.8.0.4 Core-level shifts

Code 
initial_state.x
calculates the initial state contribution
to the Core-level shift. See 
CLS_IS_example/
for
an example, and 
CLS_FS_example/
for the corresponding
final state calculation of Core-level shifts.
```
