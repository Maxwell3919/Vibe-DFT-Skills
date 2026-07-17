# 4.5 Calculation of electron-phonon interaction coefficients with the tetrahedron method

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node12.html
- Retrieved: 2026-07-17T11:51:37+00:00
- Official source SHA-256: `b31dd5ef84296d5dc25d58100739327111704ef0a582a4e8637f1baebbfcdafc`
- Extracted text SHA-256: `eeff6c1df2a41fedfdbf8fe4ec17078bbbf694a7886ac09f1e09242b60a93978`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.6 Phonons for two-dimensional crystals

Up:

4 Using PHonon

Previous:

4.4 DFPT with the tetrahedron

  

Contents

4.5 Calculation of electron-phonon interaction coefficients with the tetrahedron method

When you perform a calculation of electron-phonon interaction coefficients 
with the tetrahedron method,
you have to use an offset 
q
-point grid in order to avoid a singularity 
at 
q
= 
Γ
; you can perform this calculation as follows:

Run 
pw.x
with 
occupation = "tetrahedra_opt"
and 
K_POINT automatic
.

Run 
ph.x
with 
lshift_q = .true.
and 
electron_phonon = ""
(or unset it)
to generate the dynamical matrix and
the deformation potential (in 
_ph*/{prefix}_q*/
) of each 
q
.

Run 
ph.x
with 
electron_phonon = "lambda_tetra"
.
You should use a denser 
k
grid by setting 
nk1
, 
nk2
, and 
nk3
.
Then 
lambda*.dat
are generated; they contain 

λ
q
ν
.

Run 
alpha2f.x
with an input file as follows:

&INPUTPH
! The same as that for the electron-phonon calculation with ph.x
:
/
&INPUTA2F
nfreq = Number of frequency-points for a2F(omega), 
/

Then 
λ
, and 

ω
ln
are computed and they are printed to the standard output.

α
2
F
(
ω
) and (partial) phonon-DOS are also computed;
they are printed to a file 
prefix
.a2F.dat
.

There is an example in 
PHonon/example/tetra_example/
.
```
