# 6 Troubleshooting

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node18.html
- Retrieved: 2026-07-17T11:51:45+00:00
- Official source SHA-256: `2f75080c276461c83384a0cb7694bdb6ace70a881d435bcae93510ae432eeb4e`
- Extracted text SHA-256: `a87a470aab1fa3e1e766f1be403057082b949eb1df610a1f43ab19433ec3cb30`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

A. Appendix: Electron-phonon coefficients

Up:

User's Guide for the PHonon

Previous:

5 Parallelism

  

Contents

6 Troubleshooting

6.0.0.1 ph.x stops with 
error reading file

The data file produced by 
pw.x
is bad or incomplete or produced
by an incompatible version of the code.

6.0.0.2 ph.x mumbles something like 
cannot recover
or 
error
reading recover file

You have a bad restart file from a preceding failed execution.
Remove all files 
recover*
in 
outdir
.

6.0.0.3 ph.x says 
occupation numbers probably wrong
and
continues

You have a
metallic or spin-polarized system but occupations are not set to 

`smearing'
.

6.0.0.4 ph.x does not yield acoustic modes with zero frequency at 

$\bf q$ 
= 0

This may not be an error: the Acoustic Sum Rule (ASR) is never exactly
verified, because the system is never exactly translationally
invariant as it should be. The calculated frequency of the acoustic
mode is typically less than 10 cm
-1
, but in some cases it may be
much higher, up to 100 cm
-1
. The ultimate test is to diagonalize
the dynamical matrix with program 
dynmat.x
, imposing the ASR. If you
obtain an acoustic mode with a much smaller 
ω
(let us say 

< 1cm
-1
) 
with all other modes virtually unchanged, you can trust your results.

``The problem is [...] in the fact that the XC 
energy is computed in real space on a discrete grid and hence the
total energy is invariant (...) only for translation in the FFT
grid. Increasing the charge density cutoff increases the grid density
thus making the integral more exact thus reducing the problem,
unfortunately rather slowly...This problem is usually more severe for
GGA than with LDA because the GGA functionals have functional forms
that vary more strongly with the position; particularly so for
isolated molecules or system with significant portions of ``vacuum''
because in the exponential tail of the charge density a) the finite
cutoff (hence there is an effect due to cutoff) induces oscillations
in rho and b) the reduced gradient is diverging.''(info by Stefano de
Gironcoli, June 2008) 

6.0.0.5 ph.x yields really lousy phonons, with bad or ``negative''
frequencies or wrong symmetries or gross ASR violations

Possible reasons:

if this happens only for acoustic modes at 
$\bf q$ 
= 0 that should
have 
ω
= 0: Acoustic Sum Rule violation, see the item before
this one.

wrong data file read.

wrong atomic masses given in input will yield wrong frequencies
(but the content of file fildyn should be valid, since the force
constants, not the dynamical matrix, are written to file). 

convergence threshold for either SCF (
conv_thr
) or phonon
calculation (
tr2_ph
) too large: try to reduce them. 

maybe your system does have negative or strange phonon
frequencies, with the approximations you used. A negative frequency
signals a mechanical instability of the chosen structure. Check that
the structure is reasonable, and check the following parameters: 

The cutoff for wavefunctions, 
ecutwfc

For USPP and PAW: the cutoff for the charge density, 
ecutrho

The 
k
-point grid, especially for metallic systems.

For metallic systems: it has been observed that the convergence with
respect to the k-point grid and smearing is very slow in presence of
semicore states, and for phonon wave-vectors that are not commensurate i
with the k-point grid (that is, 

$\bf q$ 
≠
$\bf k_{i}^{}$ 
- 
$\bf k_{j}^{}$ 
)

Note that ``negative'' frequencies are actually imaginary: the negative
sign flags eigenvalues of the dynamical matrix for which 

ω
2
< 0. 

6.0.0.6 
Wrong degeneracy
error in star_q

Verify the 
q
-vector for which you are calculating phonons. In order to
check whether a symmetry operation belongs to the small group of 
$\bf q$ 
,
the code compares 
$\bf q$ 
and the rotated 
$\bf q$ 
, with an acceptance tolerance of 
10
-5
(set in routine 
PW/src/eqvect.f90
). You may run into trouble if
your 
q
-vector differs from a high-symmetry point by an amount in that
order of magnitude.

6.0.0.7 Mysterious symmetry-related errors

Symmetry-related errors like 
symmetry operation is non orthogonal
, 
or 
Wrong representation
, or 
Wrong degeneracy
, are almost 
invariably a consequence of atomic positions that are close to, 
but not sufficiently close to, symmetry positions. If such errors occur,
set the Bravais lattice using the correct 
ibrav
value (i.e. do
not use 
ibrav=0
), use Wyckoff positions if known. This must be
done in the self-consistent calculation.

Subsections

6.0.0.1 ph.x stops with 
error reading file

6.0.0.2 ph.x mumbles something like 
cannot recover
or 
error
reading recover file

6.0.0.3 ph.x says 
occupation numbers probably wrong
and
continues

6.0.0.4 ph.x does not yield acoustic modes with zero frequency at 

$\bf q$ 
= 0

6.0.0.5 ph.x yields really lousy phonons, with bad or ``negative''
frequencies or wrong symmetries or gross ASR violations

6.0.0.6 
Wrong degeneracy
error in star_q

6.0.0.7 Mysterious symmetry-related errors

next 

up 

previous 

contents 

Next:

A. Appendix: Electron-phonon coefficients

Up:

User's Guide for the PHonon

Previous:

5 Parallelism

  

Contents
```
