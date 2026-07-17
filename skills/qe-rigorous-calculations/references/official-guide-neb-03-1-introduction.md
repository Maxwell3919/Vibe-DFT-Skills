# 1 Introduction

- Official source: https://www.quantum-espresso.org/Doc/neb_user_guide/node2.html
- Retrieved: 2026-07-17T11:52:36+00:00
- Official source SHA-256: `a3d255e95ebd8dd8edc0da2bd6a9e8a782dfb0597bf021ffa191461773b7edad`
- Extracted text SHA-256: `4117b721d829f4f25f5bf0e76cfd9c6bf14ba861499bc2be54e6c7e029324bc4`
- Official Last-Modified: Mon, 08 Dec 2025 20:53:13 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2 People and terms of

Up:

User's Guide for The Quantum

Previous:

Contents

  

Contents

1 Introduction

This guide covers the usage of 
PWneb
, version 7.4: 
an open-source package for the calculation of energy barriers 
and reaction pathway using the Nudged Elastic Band (NEB) method.

This guide assumes that you know the physics 
that 
PWneb
describes and the methods it implements.
It also assumes that you have already installed,
or know how to install, Q
UANTUM 
ESPRESSO. If not, please read
the general User's Guide for Q
UANTUM 
ESPRESSO, found in 
subdirectory 
Doc/
of the main Q
UANTUM 
ESPRESSO directory,
or consult the web site:

http://www.quantum-espresso.org
.

PWneb
is part of the Q
UANTUM 
ESPRESSO distribution and uses the 
PWscf
package as electronic-structure computing tools (``engine''). 
It is however written in a modular way and could be adapted 
to use other codes as ``engine''. Since v.4.3 the NEB calculation
is performed by a separate executable 
neb.x
and no longer by 

pw.x
. Also note that NEB with Car-Parrinello molecular dynamics 
is no longer implemented since v.4.3.
```
