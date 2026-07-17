# 3.4 Optimization and dynamics

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node11.html
- Retrieved: 2026-07-17T11:50:55+00:00
- Official source SHA-256: `e4b47532119439b05f3e99a0c6ba9f28092c9df99cf541a92d965a186a558d98`
- Extracted text SHA-256: `bbd1c767c50cc9bbffe9e1643b78de3ad4aeb7341f0da2536e953a3fedc793bf`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.5 Direct interface with CASINO

Up:

3 Using PWscf

Previous:

3.3 Electronic structure calculations

  

Contents

Subsections

3.4.0.1 Structural optimization

3.4.0.2 Molecular Dynamics

3.4.0.3 Variable-cell optimization

3.4.0.4 Variable-cell molecular dynamics

3.4 Optimization and dynamics

3.4.0.1 Structural optimization

For fixed-cell optimization, specify 
calculation='relax'
and 
add namelist &IONS. All options for a single SCF calculation apply, 
plus a few others. You may follow a structural optimization with a
non-SCF band-structure calculation. See example 2.

3.4.0.2 Molecular Dynamics

Specify 
calculation='md'
, the time step 
dt
,
and possibly the number of MD stops 
nstep
.
Use variable 
ion_dynamics
in namelist &IONS
for a fine-grained control of the kind of dynamics.
Other options for setting the initial temperature
and for thermalization using velocity rescaling are available.
Remember: this is MD on the electronic ground state, not
Car-Parrinello MD.
See example 3.

3.4.0.3 Variable-cell optimization

Variable-cell calculations (both optimization and dynamics) are performed
with plane waves and G-vectors 
calculated for the starting cell
.
Only the last step, after convergence has been achieved, is performed
for the converged structure, with plane waves and G-vectors

calculated for the final cell
. Small differences between the
two last steps are thus to be expected and give an estimate of the
convergence of the variable-cell optimization with respect to the
plane-wave basis. A large difference means that you are far from
convergence in the plane-wave basis set and you need to increase the
cutoff(s) 
ecutwfc
and/or (if applicable) 
ecutrho
.

3.4.0.4 Variable-cell molecular dynamics

"A common mistake many new users make is to set the time step 
dt

improperly to the same order of magnitude as for CP algorithm, or
not setting 
dt
at all. This will produce a ``not evolving dynamics''.
Good values for the original RMW (Wentzcovitch) dynamics are 

dt

= 50÷70. The choice of the cell mass is a
delicate matter. An
off-optimal mass will make convergence slower. Too small masses, as
well as too long time steps, can make the algorithm unstable. A good
cell mass will make the oscillation times for internal degrees of
freedom comparable to cell degrees of freedom in non-damped
Variable-Cell MD. Test calculations are advisable before extensive
calculation. I have tested the damping algorithm that I have developed
and it has worked well so far. It allows for a much longer time step
(dt=

100÷150) than the RMW one and is much more stable with very
small cell masses, which is useful when the cell shape, not the
internal degrees of freedom, is far out of equilibrium. It also
converges in a smaller number of steps than RMW." (Info from Cesar Da
Silva: the new damping algorithm is the default since v. 3.1).

next 

up 

previous 

contents 

Next:

3.5 Direct interface with CASINO

Up:

3 Using PWscf

Previous:

3.3 Electronic structure calculations

  

Contents
```
