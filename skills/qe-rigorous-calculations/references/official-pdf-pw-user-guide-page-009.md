# pw_user_guide.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `b6f771e6791892ebc2c9edb7fec055364bcdccda27a0372a5db05e6a53f8aae7`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
and band calculations are not presently implemented, and 3) there are no pseudopotentials
generated for hybrid functionals. See EXX example/ and its README file, and tests pw b3lyp,
pw pbe, pw hse.

Dispersion interaction with non-local functional (vdW-DF) See example vdwDF example,
references quoted in file README therein, tests pw vdW.

Polarization via Berry Phase See example 4, its file README, the documentation in the
header of PW/src/bp c phase.f90.

Finite electric fields There are two different implementations of macroscopic electric fields
in pw.x: via an external sawtooth potential (input variable tefield=.true.) and via the
modern theory of polarizability (lelfield=.true.). The former is useful for surfaces, espe-
cially in conjunction with dipolar corrections (dipfield=.true.): see the web page – courtesy
Christoph Wolf – https://christoph-wolf.at/tag/dipfield, and PP/examples/dipole example
for an example of application. Electric fields via modern theory of polarization are documented
in example 10. The exact meaning of the related variables, for both cases, is explained in the
general input documentation.

Orbital magnetization Modern theory of orbital magnetization [Phys. Rev. Lett. 95,
137205 (2005)] for insulators. The calculation is performed by setting input variable lorbm=.true.
in nscf run. If finite electric field is present (lelfield=.true.) only Kubo terms are computed
[see New J. Phys. 12, 053032 (2010) for details].

3.4    Optimization and dynamics
Structural optimization For fixed-cell optimization, specify calculation=’relax’ and
add namelist &IONS. All options for a single SCF calculation apply, plus a few others. You
may follow a structural optimization with a non-SCF band-structure calculation. See example
2.

Molecular Dynamics Specify calculation=’md’, the time step dt, and possibly the num-
ber of MD stops nstep. Use variable ion dynamics in namelist &IONS for a fine-grained
control of the kind of dynamics. Other options for setting the initial temperature and for
thermalization using velocity rescaling are available. Remember: this is MD on the electronic
ground state, not Car-Parrinello MD. See example 3.

Variable-cell optimization Variable-cell calculations (both optimization and dynamics) are
performed with plane waves and G-vectors calculated for the starting cell. Only the last step,
after convergence has been achieved, is performed for the converged structure, with plane waves
and G-vectors calculated for the final cell. Small differences between the two last steps are thus
to be expected and give an estimate of the convergence of the variable-cell optimization with
respect to the plane-wave basis. A large difference means that you are far from convergence in
the plane-wave basis set and you need to increase the cutoff(s) ecutwfc and/or (if applicable)
ecutrho.



                                                9
```
