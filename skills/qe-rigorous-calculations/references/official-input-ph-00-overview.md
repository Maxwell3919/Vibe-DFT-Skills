# INPUT_PH — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `9d71c85b58281080e1c92c5af1036a246b9d4e248a0165ef298b9e7b28a9ae69`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
Input File Description 

Program:
ph.x / PHonon / Quantum ESPRESSO
(version: 7.5)

TABLE OF CONTENTS

INTRODUCTION

Line-of-input:

title_line

&INPUTPH

amass
| 
outdir
| 
prefix
| 
niter_ph
| 
tr2_ph
| 
alpha_mix(niter)
| 
nmix_ph
| 
verbosity
| 
reduce_io
| 
max_seconds
| 
dftd3_hess
| 
fildyn
| 
fildrho
| 
fildvscf
| 
epsil
| 
lrpa
| 
lnoloc
| 
trans
| 
lraman
| 
lmultipole
| 
eth_rps
| 
eth_ns
| 
dek
| 
recover
| 
low_directory_check
| 
only_init
| 
qplot
| 
q2d
| 
q_in_band_form
| 
electron_phonon
| 
el_ph_nsigma
| 
el_ph_sigma
| 
ahc_dir
| 
ahc_nbnd
| 
ahc_nbndskip
| 
skip_upper
| 
lshift_q
| 
zeu
| 
zue
| 
elop
| 
fpol
| 
ldisp
| 
nogg
| 
asr
| 
ldiag
| 
lqdir
| 
search_sym
| 
nq1
| 
nq2
| 
nq3
| 
nk1
| 
nk2
| 
nk3
| 
k1
| 
k2
| 
k3
| 
diagonalization
| 
read_dns_bare
| 
ldvscf_interpolate
| 
wpot_dir
| 
do_long_range
| 
do_charge_neutral
| 
start_irr
| 
last_irr
| 
nat_todo
| 
modenum
| 
start_q
| 
last_q
| 
dvscf_star
| 
drho_star

Line-of-input:

xq(1) xq(2) xq(3)

qPointsSpecs

nqs
| 
xq1
| 
xq2
| 
xq3
| 
nq

Line-of-input:

atom(1) atom(2) ... atom(nat_todo)

lmultipole
| 

ADDITIONAL INFORMATION 

INTRODUCTION

Input data format:
{ } = optional, [ ] = it depends, # = comment

Structure of the input data:

===============================================================================

title_line

&INPUTPH

...

/

[ xq(1) xq(2) xq(3) ] 
# if 
ldisp
!= .true. and 
qplot
!= .true.

[ nqs 
# if 
qplot
== .true. 

xq(1,i) xq(2,i) xq(3,1) nq(1)
...
xq(1,nqs) xq(2,nqs) xq(3,nqs) nq(nqs) ]

[ atom(1) atom(2) ... atom(nat_todo) ] 
# if 
nat_todo
was specified
```
