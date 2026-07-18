# CP2K official manual snapshot: gpw-method

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gpw.html
- Raw SHA-256: 7ac248ce6abf1011f955bf92c1e24eaf2af7d3d9be132a94fe50943d5744a001
- Status: version-matched cached official text; reopen the source for current live verification.

Gaussian Plane Wave



The primary basis in CP2K consists of Gaussian Type Orbital (GTO) functions. To take advantage of

the efficient FFT algorithm for solving the Poisson equation, the electronic density must first be

transferred from the GTO representation to a regular grid. This is referred to as

collocation

.

After solving the Poisson equation the obtained electrostatic potential has to be transferred back

into the GTO basis, which is referred to as

integration

. This ”opportunistic” switching between a

Gaussian and a plane wave representation is the core idea of the Gaussian and Plane Waves (GPW)

method. Its high-level operations are illustrated in the following flowchart:

block-beta

columns 5

a["el. Density\n(Gaussian Basis)"]

space

b["el. Density\n(Regular Grid)"]

space

c["el. Density\n(Plane Waves)"]

space space space space space

f["el. Potenial\n(Gaussian Basis)"]

space

e["el. Potenial\n(Regular Grid)"]

space

d["el. Potenial\n(Plane Waves)"]

a -- "Collocate" --> b

b -- "FFT" --> c

c -- "Poisson Solver" --> d

d -- "FFT<sup>-1</sup>" --> e

e -- "Integrate" --> f

See also



https://www.cp2k.org/gpw

https://www.cp2k.org/quickstep

Lippert1997

Kühne2020
