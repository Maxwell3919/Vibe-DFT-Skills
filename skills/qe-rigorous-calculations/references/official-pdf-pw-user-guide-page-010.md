# pw_user_guide.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `df77cf65e2c4b5399254d97c2ba5d861f85206c8ba3e9c4cc42d0282c9d5c20f`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Variable-cell molecular dynamics ”A common mistake many new users make is to set the
time step dt improperly to the same order of magnitude as for CP algorithm, or not setting
dt at all. This will produce a “not evolving dynamics”. Good values for the original RMW
(Wentzcovitch) dynamics are dt = 50 ÷ 70. The choice of the cell mass is a delicate matter.
An off-optimal mass will make convergence slower. Too small masses, as well as too long time
steps, can make the algorithm unstable. A good cell mass will make the oscillation times for
internal degrees of freedom comparable to cell degrees of freedom in non-damped Variable-Cell
MD. Test calculations are advisable before extensive calculation. I have tested the damping
algorithm that I have developed and it has worked well so far. It allows for a much longer
time step (dt=100 ÷ 150) than the RMW one and is much more stable with very small cell
masses, which is useful when the cell shape, not the internal degrees of freedom, is far out of
equilibrium. It also converges in a smaller number of steps than RMW.” (Info from Cesar Da
Silva: the new damping algorithm is the default since v. 3.1).

3.5    Direct interface with CASINO
PWscf supports the Quantum Monte Carlo program CASINO directly. For more information
on the CASINO code, see https://vallico.net/casinoqmc. CASINO may take the output of
PWSCF and ’improve it’ giving considerably more accurate total energies and other quantities
than DFT is capable of.
   PWscf users wishing to learn how to use CASINO may like to attend one of the annual
CASINO summer schools in Mike Towler’s ”Apuan Alps Centre for Physics” in Tuscany, Italy.
More information can be found at http://www.vallico.net/tti/tti.html

Practicalities The interface between PWscf and CASINO is provided through a file with a
standard format containing geometry, basis set, and orbital coefficients, which PWscf will pro-
duce on demand. For SCF calculations, the name of this file may be pwfn.data, bwfn.data or
bwfn.data.b1 depending on user requests (see below). If the files are produced from an MD
run, the files have a suffix .0001, .0002, .0003 etc. corresponding to the sequence of timesteps.
   CASINO support is implemented by three routines in the PW directory of the espresso distri-
bution:

    pw2casino.f90 : the main routine

    pw2casino write.f90 : writes the CASINO xwfn.data file in various formats

    pw2blip.f90 : does the plane-wave to blip conversion, if requested

Relevant behavior of PWscf may be modified through an optional auxiliary input file, named
pw2casino.dat (see below).

How to generate xwfn.data files with PWscf Use the ’-pw2casino’ option when invoking
pw.x, e.g.:

pw.x -pw2casino < input_file > output_file

The xfwn.data file will then be generated automatically.



                                               10
```
