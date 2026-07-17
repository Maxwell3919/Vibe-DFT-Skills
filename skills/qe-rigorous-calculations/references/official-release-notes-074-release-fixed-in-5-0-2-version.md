# Quantum ESPRESSO release notes — Fixed in 5.0.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `ef73b44dabfaf30205f4075c1700449401f06b49b34f13d794eb36c4b64141a3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.0.2 version:

  * the random-number generator wasn't checking for incorrect seeding;
    under some unlikely circumstances this might lead to strange errors
  * k-point parallelization in v.5.0 and 5.0.1 was affected by a subtle 
    problem: the distribution of plane waves was not always the same on 
    all pools of processors. While results were still correct, strange
    problems (e.g. lockups) could result. Also: there are more and more
    machines that are not able to produce the same results starting from
    the same data on different processors. Charge-density mixing is now
    performed on one pool, broadcast to all others, to prevent trouble.
  * upftools: fhi2upf converter of v.5 introduced a small error in some cases
  * Small error in the calculation of rPW86 functional, due to a mismatch
    between its previous definition (Slater exchange contained in GGA) and
    the check on the rho=>0, grad rho=>0 limits. Note that a similar problem
    might also affect hcth, olyp, m06l functionals. 
    The new PBEQ2D functional (introduced in 5.0.1) was also not correct.
  * NEB calculation can get stuck if the code tries to read &ions namelist
    in the PWscf-related input section
  * NEB: spurious blank character appearing in lines longer than 80 characters
    with Intel compiler (same problem that was previously fixed in PWscf)
  * PH: bug in symmetrization in some special cases (supercells of graphene)
  * PH: bug in restart when the code stops during self consistency
  * PH: ph.x with images wasn't working any longer 
  * PH: electron_phonon='simple' wasn't working together with ldisp=.true.
  * PH: images with a single q point were not collecting properly the files.
  * PH: grid splitting of irrep + single q point + wf_collect=.true. 
    was not working

                               * * * * *
```
