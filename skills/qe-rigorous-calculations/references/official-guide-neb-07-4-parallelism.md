# 4 Parallelism

- Official source: https://www.quantum-espresso.org/Doc/neb_user_guide/node6.html
- Retrieved: 2026-07-17T11:52:42+00:00
- Official source SHA-256: `94d0e57187ec93bc10ebdec2aaedc1320066f6a138f414c799954db9d63e18da`
- Extracted text SHA-256: `925617ab317bc9743d519b32f861cc6b302cf2ebf92ce205ef3082241d7b9d31`
- Official Last-Modified: Mon, 08 Dec 2025 20:53:13 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

5 Using PWneb

Up:

User's Guide for The Quantum

Previous:

3.1 Running examples

  

Contents

4 Parallelism

The 
PWneb
code is interfaced to 
PWscf
, which is used as computational engine 
for total energies and forces. It can therefore take advantage from the two 
parallelization paradigms currently implemented in Q
UANTUM 
ESPRESSO, namely
Message Passing Interface (MPI) and OpenMP threads, and exploit
all 
PWscf
-specific parallelization options.
For a detailed information about parallelization in Q
UANTUM 
ESPRESSO, 
please refer to the general documentation.

In addition, 
PWneb
makes several independent evaluations
of energy and forces at each step of the path optimization:
one per ``image'', that is, a point in the path, corresponding
to a set of atomic positions.
It is thus possible and often convenient to distribute
images among processors, using the ``image'' parallelization,
as described in the general documentation. The number of image
groups is specified using the option 
-ni N
(or,
equivalently, 
-nimage N
) after the executable name
(e.g., 
neb.x
) in the command line. The default is a single
image group (no image parallelization)

Images are loosely coupled calculations: processors belonging to
different image groups communicate only once in a while, whereas
processors within the same image group are tightly coupled and 
communications are more significant (please refer to the user
guide of 
PWscf
).
```
