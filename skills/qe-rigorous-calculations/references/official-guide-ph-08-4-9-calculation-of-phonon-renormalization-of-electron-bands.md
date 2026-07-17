# 4.9 Calculation of phonon-renormalization of electron bands

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node16.html
- Retrieved: 2026-07-17T11:51:42+00:00
- Official source SHA-256: `b9aa5e08fa87f47ca3ff0a53d8112e3d860f79f7eb5db57aaef2ef70d9130850`
- Extracted text SHA-256: `1b944b3870f2de0d499d97545245bac4d595ce64f24472a72ae58eb812de6519`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

5 Parallelism

Up:

4 Using PHonon

Previous:

4.8 Fourier interpolation of phonon

  

Contents

4.9 Calculation of phonon-renormalization of electron bands

The phonon-induced renormalization of electron bands can be computed using 
PHonon
.
After SCF, PHONON, and NSCF calculations, one can run 
ph.x
with the

electron_phonon=`ahc'
option, which generates binary files containing
quantities required for the calculation of electron self-energy.
Then, a 
postahc.x
run reads these binary files and compute the
phonon-induced electron self-energy at a given temperature.

For more details, see the 
PHonon/Doc/dfpt_self_energy.pdf
file.

Also, there is an example in 
PHonon/example/example19/
.

Implementation of this functionality in Q
UANTUM 
ESPRESSO is described in the following
paper:

J.-M. Lihm and C.-H. Park, Phys. Rev. B 
101
, 121102 (2020).
```
