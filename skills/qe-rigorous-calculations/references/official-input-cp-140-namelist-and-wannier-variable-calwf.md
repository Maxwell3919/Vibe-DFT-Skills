# INPUT_CP — NAMELIST: &WANNIER — Variable: calwf

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `002f2d922c493b86183d565add56b400bf559a14d1b817bd3163b61051b3c83f`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       calwf
   
   Type:           INTEGER
   Default:        3
   Description:    Wannier Function Options, can be 1,2,3,4,5
                   
                   1. Output the Wannier function density, nwf and wffort
                      are used for this option. see below.
                   2. Output the Overlap matrix O_i,j=<w_i|exp{iGr}|w_j>. O is
                      written to unit 38. For details on how O is constructed,
                      see below.
                   3. Perform nsteps of Wannier dynamics per CP iteration, the
                      orbitals are now Wannier Functions, not Kohn-Sham orbitals.
                      This is a Unitary transformation of the occupied subspace
                      and does not leave the CP Lagrangian invariant. Expectation
                      values remain the same. So you will **NOT** have a constant
                      of motion during the run. Don't freak out, its normal.
                   4. This option starts for the KS states and does 1 CP iteration
                      and nsteps of Damped-Dynamics to generate  maximally
                      localized wannier functions. Its useful when you have the
                      converged KS groundstate and want to get to the converged
                      Wannier function groundstate in 1 CP Iteration.
                   5. This option is similar to calwf 1, except that the output is
                      the Wannier function/wavefunction, and not the orbital
                      density. See nwf below.
   +--------------------------------------------------------------------
   
```
