# A. Appendix: Electron-phonon coefficients

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node19.html
- Retrieved: 2026-07-17T11:51:47+00:00
- Official source SHA-256: `4278c09e7b89f61ce1ceee6d129a192ff40729a05b92c4cb2cc9e20ecbbb8cc3`
- Extracted text SHA-256: `3a17599a9adca5304c5d49db825a45ef41ebb9beb4f129b4d3faf2d9759746a4`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

About this document ...

Up:

User's Guide for the PHonon

Previous:

6 Troubleshooting

  

Contents

A. Appendix: Electron-phonon coefficients

The electron-phonon coefficients 
g

are defined as

g
$\scriptstyle \bf q$ 
ν
(
$\displaystyle \bf k$ 
, 
i
, 
j
) = 
$\displaystyle \left(\vphantom{{\hbar\over 2M\omega_{{\bf q}\nu}}}\right.$ 
$\displaystyle {\hbar\over 2M\omega_{{\bf q}\nu}}$ 
$\displaystyle \left.\vphantom{{\hbar\over 2M\omega_{{\bf q}\nu}}}\right)^{{1/2}}_{}$ 
〈
ψ
i,
$\scriptstyle \bf k$ 
|
$\displaystyle {dV_{SCF}\over d {\hat u}_{{\bf q}\nu}}$ 
⋅
$\displaystyle \hat{\epsilon}_{{{\bf q}\nu}}^{}$ 
| 
ψ
j,
$\scriptstyle \bf k$ 
+
$\scriptstyle \bf q$ 
〉.

(1)

The phonon linewidth 

γ
$\scriptstyle \bf q$ 
ν
is defined by

γ
$\scriptstyle \bf q$ 
ν
= 2
πω
$\scriptstyle \bf q$ 
ν
$\displaystyle \sum_{{ij}}^{}$ 
$\displaystyle \int$ 
$\displaystyle {d^3k\over \Omega_{BZ}}$ 
| 
g
$\scriptstyle \bf q$ 
ν
(
$\displaystyle \bf k$ 
, 
i
, 
j
)|
2
δ
(
e
$\scriptstyle \bf q$ 
, i
- 
e
F
)
δ
(
e
$\scriptstyle \bf k$ 
+
$\scriptstyle \bf q$ 
, j
- 
e
F
),

(2)

while the electron-phonon coupling constant 

λ
$\scriptstyle \bf q$ 
ν
for
mode 
ν
at wavevector 
$\bf q$ 
is defined as

λ
$\scriptstyle \bf q$ 
ν
= 
$\displaystyle {\gamma_{{\bf q}\nu} \over \pi\hbar N(e_F)\omega^2_{{\bf q}\nu}}$ 

(3)

where 
N
(
e
F
) is the DOS at the Fermi level.
The spectral function is defined as

α
2
F
(
ω
) = 
$\displaystyle {1\over 2\pi N(e_F)}$ 
$\displaystyle \sum_{{{\bf q}\nu}}^{}$ 
δ
(
ω
- 
ω
$\scriptstyle \bf q$ 
ν
)
$\displaystyle {\gamma_{{\bf q}\nu}\over\hbar\omega_{{\bf q}\nu}}$ 
.

(4)

The electron-phonon mass enhancement parameter 
λ

can also be defined as the first reciprocal momentum of 
the spectral function:

λ
= 
$\displaystyle \sum_{{{\bf q}\nu}}^{}$ 
λ
$\scriptstyle \bf q$ 
ν
= 2
$\displaystyle \int$ 
$\displaystyle {\alpha^2F(\omega) \over \omega}$ 
dω
.

(5)

Note that a factor 
M
-1/2
is hidden in the definition of
normal modes as used in the code.

McMillan:

T
c
= 
$\displaystyle {\Theta_D \over 1.45}$ 
exp
$\displaystyle \left[\vphantom{
{-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}}\right.$ 
$\displaystyle {-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}$ 
$\displaystyle \left.\vphantom{
{-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}}\right]$ 

(6)

or (better?)

T
c
= 
$\displaystyle {\omega_{log}\over 1.2}$ 
exp
$\displaystyle \left[\vphantom{
{-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}}\right.$ 
$\displaystyle {-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}$ 
$\displaystyle \left.\vphantom{
{-1.04(1+\lambda)\over \lambda(1-0.62\mu^*)-\mu^*}}\right]$ 

(7)

where

ω
log
= exp
$\displaystyle \left[\vphantom{ {2\over\lambda} \int {d\omega\over\omega}
\alpha^2F(\omega) \mbox{log}\omega }\right.$ 
$\displaystyle {2\over\lambda}$ 
$\displaystyle \int$ 
$\displaystyle {d\omega\over\omega}$ 
α
2
F
(
ω
)log
ω
$\displaystyle \left.\vphantom{ {2\over\lambda} \int {d\omega\over\omega}
\alpha^2F(\omega) \mbox{log}\omega }\right]$ 

(8)

next 

up 

previous 

contents 

Next:

About this document ...

Up:

User's Guide for the PHonon

Previous:

6 Troubleshooting

  

Contents
```
