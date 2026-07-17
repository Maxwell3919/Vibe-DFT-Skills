# 4.1 Execution time

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node15.html
- Retrieved: 2026-07-17T11:51:02+00:00
- Official source SHA-256: `dc6b028ba337b44b268c2ee43cba79f83dc6a23b816a449f4b98dc56d556d236`
- Extracted text SHA-256: `20f3a8364814dc1dc11543b539bc35e96b0ada14bf42575a1be9807a0981f112`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.2 Memory requirements

Up:

4 Performances

Previous:

4 Performances

  

Contents

4.1 Execution time

The following is a rough estimate of the complexity of a plain
scf calculation with 
pw.x
, for NCPP. USPP and PAW 
give raise additional terms to be calculated, that may add from a 
few percent 
up to 30-40% to execution time. For phonon calculations, each of the
3
N
at
modes requires a time of the same order of magnitude of
self-consistent calculation in the same system (possibly times a small multiple). 
For 
cp.x
, each time step takes something in the order of

T
h
+ 
T
orth
+ 
T
sub
defined below.

The time required for the self-consistent solution at fixed ionic
positions, 
T
scf
, is:

T
scf
= 
N
iter
T
iter
+ 
T
init

where 
N
iter
= number of self-consistency iterations (
niter
), 

T
iter
=
time for a single iteration, 
T
init
= initialization time
(usually much smaller than the first term).

The time required for a single self-consistency iteration 
T
iter
is:

T
iter
= 
N
k
T
diag
+ 
T
rho
+ 
T
scf

where 
N
k
= number of k-points, 
T
diag
= time per 
Hamiltonian iterative diagonalization, 
T
rho
= time for charge density 
calculation, 
T
scf
= time for Hartree and XC potential
calculation.

The time for a Hamiltonian iterative diagonalization 
T
diag
is:

T
diag
= 
N
h
T
h
+ 
T
orth
+ 
T
sub

where 
N
h
= number of 
Hψ
products needed by iterative diagonalization,

T
h
= time per 
Hψ
product, 
T
orth
= CPU time for 
orthonormalization, 
T
sub
= CPU time for subspace diagonalization.

The time 
T
h
required for a 
Hψ
product is

T
h
= 
a
1
MN
+ 
a
2
MN
1
N
2
N
3
log
(
N
1
N
2
N
3
) + 
a
3
MPN
.

The first term comes from the kinetic term and is usually much smaller
than the others. The second and third terms come respectively from local
and nonlocal potential. 

a
1
, 
a
2
, 
a
3
are prefactors (i.e.
small numbers 

$\cal {O}$ 
(1)), 
M
= number of valence
bands (
nbnd
), 
N
= number of PW (basis set dimension: 
npw
), 

N
1
, 
N
2
, 
N
3
=
dimensions of the FFT grid for wavefunctions (
nr1s
, 
nr2s
,

nr3s
; 

N
1
N
2
N
3
∼8
N
), 
P = number of pseudopotential projectors, summed on all atoms, on all values of the
angular momentum 
l
, and 

m
= 1,..., 2
l
+ 1.

The time 
T
orth
required by orthonormalization is

T
orth
= 
b
1
NM
x
2

and the time 
T
sub
required by subspace diagonalization is

T
sub
= 
b
2
M
x
3

where 
b
1
and 
b
2
are prefactors, 
M
x
= number of trial wavefunctions 
(this will vary between 
M
and 2÷4
M
, depending on the algorithm).

The time 
T
rho
for the calculation of charge density from wavefunctions is

T
rho
= 
c
1
MN
r1
N
r2
N
r3
log
(
N
r1
N
r2
N
r3
) + 
c
2
MN
r1
N
r2
N
r3
+ 
T
us

where 

c
1
, 
c
2
, 
c
3
are prefactors, 

N
r1
, 
N
r2
, 
N
r3
=
dimensions of the FFT grid for charge density (
nr1
,

nr2
, 
nr3
; 

N
r1
N
r2
N
r3
∼8
N
g
,
where 
N
g
= number of G-vectors for the charge density,

ngm
), and 

T
us
= time required by PAW/USPPs contribution (if any).
Note that for NCPPs the FFT grids for charge and
wavefunctions are the same.

The time 
T
scf
for calculation of potential from charge density is

T
scf
= 
d
2
N
r1
N
r2
N
r3
+ 
d
3
N
r1
N
r2
N
r3
log
(
N
r1
N
r2
N
r3
)

where 
d
1
, 
d
2
are prefactors.

For hybrid DFTs, the dominant term is by far the calculation of the 
nonlocal (
V
x
ψ
) product, taking as much as

T
exx
= 
eN
k
N
q
M
2
N
1
N
2
N
3
log
(
N
1
N
2
N
3
)

where 
N
q
is the number of points in the 
k
+ 
q
grid, determined by
options 
nqx1,nqx2,nqx3
, 
e
is a prefactor.

The above estimates are for serial execution. In parallel execution,
each contribution may scale in a different manner with the number of processors (see below).

next 

up 

previous 

contents 

Next:

4.2 Memory requirements

Up:

4 Performances

Previous:

4 Performances

  

Contents
```
