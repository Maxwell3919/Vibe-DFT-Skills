# 4.2 Memory requirements

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node16.html
- Retrieved: 2026-07-17T11:51:03+00:00
- Official source SHA-256: `051ab39b9bb29baacee52c23bfad8186b4f215b170e3695515be89e845e97a04`
- Extracted text SHA-256: `ba71621640276a2bdab6620d5b01d9f7317c82459ef82cb14e2f079309343849`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.3 File space requirements

Up:

4 Performances

Previous:

4.1 Execution time

  

Contents

4.2 Memory requirements

A typical self-consistency or molecular-dynamics run requires a maximum
memory in the order of 
O
double precision complex numbers, where

O
= 
mMN
+ 
PN
+ 
pN
1
N
2
N
3
+ 
qN
r1
N
r2
N
r3

with 
m
, 
p
, 
q
= small factors; all other variables have the same meaning as
above. Note that if the 
Γ
-point only (
k
= 0) is used to sample the 
Brillouin Zone, the value of N will be cut into half.

For hybrid DFTs, additional storage of 
O
x
double precision complex 
numbers is needed (for Fourier-transformed Kohn-Sham states), with

O
x
= 
xN
q
MN
1
N
2
N
3
and 
x
= 0.5 for 
Γ
-only 
calculations, 
x
= 1 otherwise.

The memory required by the phonon code follows the same patterns, with
somewhat larger factors 
m
, 
p
, 
q
.
```
