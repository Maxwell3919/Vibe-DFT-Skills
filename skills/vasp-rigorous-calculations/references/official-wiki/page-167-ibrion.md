# IBRION

- Official URL: https://www.vasp.at/wiki/IBRION
- Page ID: 167
- Revision ID: 37190
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

IBRION = -1 | 0 | 1 | 2 | 3 | 5 | 6 | 7 | 8 | 11 | 12 | 40 | 44

Default: IBRION

= -1

for NSW=−1 or 0

= 0

else

Description: determines how the crystal structure changes during the calculation:

- no update

- IBRION = -1 (Avoid setting IBRION = -1 with NSW > 0 to prevent recomputing the same structure NSW times).

- Molecular dynamics

- IBRION = 0

- Structure optimization

- IBRION = 1 RMM-DIIS

- IBRION = 2 conjugate gradient

- IBRION = 3 damped molecular dynamics

- Computing phonon modes

- IBRION = 5 finite differences without symmetry (deprecated; use 6 instead)

- IBRION = 6 finite differences with symmetry

- IBRION = 7 perturbation theory without symmetry (deprecated; use 8 instead)

- IBRION = 8 perturbation theory with symmetry

- Analyzing transition states

- IBRION = 40 intrinsic-reaction-coordinate calculations

- IBRION = 44 improved dimer method

- User-supplied interactive changes

- IBRION = 11 from standard input

- IBRION = 12 from Python plugin

Contents

- 1 Molecular dynamics

- 2 Structure optimization

- 3 Computing the phonon modes

- 4 Analyzing transition states

- 5 Interactively supplied positions and lattice vectors

- 6 Related tags and articles

Molecular dynamics[edit | edit source]

In molecular-dynamics (MD) simulations the positions of the ions are updated using a classical equation of motion for the ions. There are several algorithms for the time propagation in MD controlled by selecting MDALGO and the choice of the thermostats. The MD run performs NSW timesteps of length POTIM.

Frequently, performing an ab-initio calculations in every step of an MD simulation is too expensive so that machine-learned force fields are needed.

Tip: In order to limit the output of the MD simulation, control the verbosity by setting NWRITE=0,1, or reduce the frequency of output using ML_OUTBLOCK, NBLOCK, or KBLOCK.

Structure optimization[edit | edit source]

VASP optimizes the structure based on the degrees of freedom selected with the ISIF tag and (if used) the selective dynamics POSCAR file.
Generally, the larger the number of degrees of freedom, the harder it is to find the optimal solution.
To find the solution, VASP provides multiple algorithms:

- RMM-DIIS (IBRION = 1) reduces the forces by linear combination of previous positions. It is the method of choice for larger systems (>20 degrees of freedom) that are reasonably close to the ground-state structure.

- Conjugate gradient (IBRION = 2) finds the optimal step size along a search direction. It is a robust default choice but may need more iterations than RMM-DIIS.

- Damped molecular dynamics (IBRION = 3) runs a MD simulation with decreasing velocity of the ions. Use this for large systems far away from the minimum to get to a better starting point for the other algorithms.

Consult the structure optimization page for advise on how to choose the optimization algorithm.

Computing the phonon modes[edit | edit source]

The second-order derivatives of the total energy [math]\displaystyle{ E }[/math] with respect to ionic positions [math]\displaystyle{ R_{\alpha i} }[/math] of ion [math]\displaystyle{ \alpha }[/math] in the direction [math]\displaystyle{ i }[/math], is computed using a first-order derivative of the forces [math]\displaystyle{ F_{\beta j} }[/math]. Then, the dynamical matrix [math]\displaystyle{ D_{\alpha i \beta j} }[/math] is constructed, diagonalized, and the phonon modes and frequencies of the system are reported in the OUTCAR file and vaspout.h5. Also see theory on phonons.

Tip: It may be necessary to set EDIFF <= 1E-6 because the default (EDIFF = 1E-4) often results in unacceptably large errors.

VASP implements two different methods to compute the phonon modes and can use symmetry to reduce the number of computed displacements:

- IBRION = 5 finite differences without symmetry

- IBRION = 6 finite differences with symmetry

- IBRION = 7 density-functional-perturbation theory without symmetry

- IBRION = 8 density-functional-perturbation theory with symmetry

It is strongly recommended to use symmetry (6 or 8), as this can reduce the computational effort by several orders of magnitude without sacrifying accuracy.
For finite differences, the elastic tensors and internal strain tensors are computed for ISIF >= 3.
Compute Born-effective charges, piezoelectric constants, and the ionic contribution to the dielectric tensor by specifying LEPSILON = .TRUE. (linear response theory) or LCALCEPS = .TRUE. (finite external field).

Also see computing the phonon dispersion and DOS.

Analyzing transition states[edit | edit source]

To study the kinetics of chemical reactions, one may want to construct transition states or follow the reaction path.
For the analysis of transition states the following methods are available:

- Setting IBRION = 40, you can start from a transition state and monitor the energy along an intrinsic-reaction coordinate (IRC). The IRC calculations section describes this method.

- With the improved dimer method (IBRION = 44), you can search for a the transition state starting from an arbitrary structure in the investigated phase space.

- The nudged elastic bands method finds an approximate reaction path based on the initial and final structure, i.e., reactant and product.

Interactively supplied positions and lattice vectors[edit | edit source]

Occasionally, you may want to run VASP for related structures where the overhead of restarting VASP is significant.
In these scenarios, VASP provides the following alternatives

- With IBRION = 11, you can provide new structures via the standard input, cf. the INTERACTIVE tag. For ISIF >= 3, a complete POSCAR file is read, otherwise just the positions in fractional coordinates.

- If you linked VASP with Python, you can write a Python plugin to modify the structure. Set IBRION = 12 or PLUGINS/STRUCTURE = T to activate it.

Related tags and articles[edit | edit source]

Related tags: NSW,
POTIM,
MDALGO,
SMASS,
NFREE,
ISIF,
LEPSILON,
LCALCEPS

Related files: POSCAR, CONTCAR, XDATCAR, vaspout.h5

Related topics and how-to pages: Time-propagation algorithms in molecular dynamics,
Structure optimization,
Selective dynamics,
Computing the phonon dispersion and DOS,
Transition states,
IRC calculations,
Improved Dimer Method,
Writing a Python plugin

Examples that use this tag
