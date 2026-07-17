# User's Guide for the PWscf package

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/
- Retrieved: 2026-07-17T11:50:50+00:00
- Official source SHA-256: `5371f10c2e78ea48b6d33828d4192bb6f981cbce986e14fd67176e035c9965e4`
- Extracted text SHA-256: `c8be18b74071ee5f86ef8c19163262ca9cf20a5a6f9f44e8fb84b4e392defe59`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

Contents

  

Contents

\includegraphics[width=5cm]{../../../Doc/quantum_espresso} 

PWscf
User's Guide (v.7.5) 

Contents

1 Introduction

1.1 What can 
PWscf
do

1.2 People

1.3 Terms of use

2 Compilation

3 Using 
PWscf

3.1 Input data

3.2 Data files

3.3 Electronic structure calculations

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

3.4 Optimization and dynamics

3.4.0.1 Structural optimization

3.4.0.2 Molecular Dynamics

3.4.0.3 Variable-cell optimization

3.4.0.4 Variable-cell molecular dynamics

3.5 Direct interface with 
CASINO

3.5.0.1 Practicalities

3.5.0.2 How to generate 
xwfn.data
files with 
PWscf

3.6 Socket interface with i-PI

3.6.0.1 Practicalities

3.6.0.2 How to use the i-PI inteface

3.6.0.3 Advanced i-PI usage

4 Performances

4.1 Execution time

4.2 Memory requirements

4.3 File space requirements

4.4 Parallelization issues

4.5 Understanding the time report

4.5.1 Serial execution

4.5.2 Parallel execution

4.5.2.1 Quick estimate of parallelization parameters

4.5.2.2 Automatic guess of parallelization parameters

4.5.2.3 Typical symptoms of bad/inadequate parallelization

4.6 Restarting

4.6.1 Signal trapping (experimental!)

5 Troubleshooting

5.0.0.1 pw.x says 'error while loading shared libraries' or
'cannot open shared object file' and does not start

5.0.0.2 errors in examples with parallel execution

5.0.0.3 pw.x prints the first few lines and then nothing happens
(parallel execution)

5.0.0.4 pw.x stops with error while reading data

5.0.0.5 pw.x mumbles something like 
cannot recover
or 

error reading recover file

5.0.0.6 pw.x stops with 
inconsistent DFT
error

5.0.0.7 pw.x stops with error in cdiaghg or rdiaghg

5.0.0.8 pw.x crashes with no error message at all

5.0.0.9 pw.x crashes with 
segmentation fault
or similarly
obscure messages

5.0.0.10 pw.x works for simple systems, but not for large systems
or whenever more RAM is needed

5.0.0.11 pw.x crashes with 
error in davcio

5.0.0.12 pw.x crashes in parallel execution with an obscure message
related to MPI errors

5.0.0.13 pw.x stops with error message 
the system is metallic,
specify occupations

5.0.0.14 pw.x stops with 
internal error: cannot bracket Ef

5.0.0.15 pw.x yields 
internal error: cannot bracket Ef
message 
but does not stop

5.0.0.16 pw.x runs but nothing happens

5.0.0.17 pw.x yields weird results

5.0.0.18 FFT grid is machine-dependent

5.0.0.19 pw.x does not find all the symmetries you expected

5.0.0.20 Self-consistency is slow or does not converge at all

5.0.0.21 I do not get the same results in different machines!

5.0.0.22 Execution time is time-dependent!

5.0.0.23 
Warning : N eigenvectors not converged

5.0.0.24 
Warning : negative or imaginary charge...
, or 

...core charge ...
, or 
npt with rhoup< 0...
or 
rho dw< 0...

5.0.0.25 Structural optimization is slow or does not converge or ends 
with a mysterious bfgs error

5.0.0.26 pw.x stops during variable-cell optimization in
checkallsym with 
non orthogonal operation
error

About this document ...
```
