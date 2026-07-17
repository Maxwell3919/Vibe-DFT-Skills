# 2 People and terms of use

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node3.html
- Retrieved: 2026-07-17T11:52:18+00:00
- Official source SHA-256: `a69d8aa460cc5c0ee9673369e4b36a9ff13c62f2eada7969a29185abbaf5a5c4`
- Extracted text SHA-256: `aebd3d874926fad555aed381363edb793ab64ac5d6d4542bcbfe410510dbd1dc`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3 Compilation

Up:

User's Guide for the PP

Previous:

1 Introduction

  

Contents

2 People and terms of use

The 
PostProc
package was originally developed by Stefano Baroni, 
Stefano de Gironcoli, Andrea Dal Corso (SISSA), Paolo Giannozzi 
(Univ. Udine), and many others. We mention in particular: 

Dong Yang and Qin Liu (JSG) for calculation of DORI (10.1021/ct500490b)
and for spin-polarized ELF;

Minsu Ghim (Seoul National U.) for Ji Hoon Ryoo's spin-current matrix
elements (Phys. Rev. B 99, 235113) for spin Hall conductivity using
Wannier interpolation, in pw2wannier.f90;

Yang Jiao, Elsebeth Schröder, Per Hyldgaard (Chalmers) for the

ppacf.x
code;

Alberto Otero-de-la-Roza for the 
pw2critic.x
utility;

Junfeng Qiao for improvements to 
plotband.x
;

Olivia Pulci, Adriano Mosca Conte, Davide Grassano (RomaII)
for the 
pw2gw
utility;

Cyrille Barreteau and Alexander Smogunov (CEA) for 
magnetic anisotropy with the Force Theorem in 
projwfc.f90
;

Andrea Benassi (SISSA) for the 
epsilon
utility,
Tae Yun Kim and Cheol-Hwan Park (Seoul National University)
for fixes to it;

Dmitry Korotin (Inst. Met. Phys. Ekaterinburg) for the

wannier_ham
utility;

Georgy Samsonidze (Bosch Research) for the interface
with the Berkeley GW code, Fangzhou Zhao (Berkeley) 
for its extension to hybrid and meta-GGA functionals;

The late Prof. Eyvaz Isaev for the Fermi Surface code;

Natalie Holzwarth (WFU) for the PAW projection in code

projwfc.f90
;

Takashi Koretsune and Florian Thoele (ETHZ) for noncollinear 
magnetisation support with USPP and PAW pseudopotentials in 
code 
pw2wannier.f90
.

Leopold Talirz (U.York) for extensions and fixes to 
pp.x
.

Iurii Timrov (PSI) for the implementation of 
wannier2pw.f90
.

PostProc
is free software, released under the 
GNU General Public License. See:

http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
, 
or the file License in the distribution).

We shall greatly appreciate if scientific work done using the Q
UANTUM 
ESPRESSO 
distribution will contain an acknowledgment to the following references:

P. Giannozzi, S. Baroni, N. Bonini, M. Calandra, R. Car, C. Cavazzoni,
D. Ceresoli, G. L. Chiarotti, M. Cococcioni, I. Dabo, A. Dal Corso,
S. Fabris, G. Fratesi, S. de Gironcoli, R. Gebauer, U. Gerstmann,
C. Gougoussis, A. Kokalj, M. Lazzeri, L. Martin-Samos, N. Marzari,
F. Mauri, R. Mazzarello, S. Paolini, A. Pasquarello, L. Paulatto,
C. Sbraccia, S. Scandolo, G. Sclauzero, A. P. Seitsonen, A. Smogunov,
P. Umari, R. M. Wentzcovitch,
J.Phys.: Condens.Matter 21, 395502 (2009)

and

P. Giannozzi, O. Andreussi, T. Brumme, O. Bunau, M. Buongiorno Nardelli, 
M. Calandra, R. Car, C. Cavazzoni, D. Ceresoli, M. Cococcioni, N. Colonna, 
I. Carnimeo, A. Dal Corso, S. de Gironcoli, P. Delugas, R. A. DiStasio Jr,
A. Ferretti, A. Floris, G. Fratesi, G. Fugallo, R. Gebauer, U. Gerstmann,
F. Giustino, T. Gorni, J Jia, M. Kawamura, H.-Y. Ko, A. Kokalj, 
E. Küçükbenli, M .Lazzeri, M. Marsili, N. Marzari, F. Mauri, 
N. L. Nguyen, H.-V. Nguyen, A. Otero-de-la-Roza, L. Paulatto, S. Poncé, 
D. Rocca, R. Sabatini, B. Santra, M. Schlipf, A. P. Seitsonen, A. Smogunov,
I. Timrov, T. Thonhauser, P. Umari, N. Vast, X. Wu, S. Baroni,
J.Phys.: Condens.Matter 29, 465901 (2017)

Users of the GPU-enabled version should also cite the following paper:

P. Giannozzi, O. Baseggio, P. Bonfà, D. Brunato, R. Car, I. Carnimeo,
C. Cavazzoni, S. de Gironcoli, P. Delugas, F. Ferrari Ruffino,
A. Ferretti, N. Marzari, I. Timrov, A. Urru, S. Baroni, 
J. Chem. Phys. 152, 154105 (2020)

Note the form Q
UANTUM 
ESPRESSO for textual citations of the code.
Please also see package-specific documentation for
further recommended citations.
Pseudopotentials should be cited as (for instance)

[ ] We used the pseudopotentials C.pbe-rrjkus.UPF
and O.pbe-vbc.UPF from

http://www.quantum-espresso.org
.

next 

up 

previous 

contents 

Next:

3 Compilation

Up:

User's Guide for the PP

Previous:

1 Introduction

  

Contents
```
