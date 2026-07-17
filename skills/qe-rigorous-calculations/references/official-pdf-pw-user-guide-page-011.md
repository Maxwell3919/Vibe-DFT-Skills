# pw_user_guide.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `2708c68e1313e620ac9e8a5e4cc94cdeb2e40ddf4aafe9a3d2e7922ba1f75a55`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    PWscf is capable of doing the plane wave to blip conversion directly (the ’blip’ utility
provided in the CASINO distribution is not required) and so by default, PWscf produces the
’binary blip wave function’ file bwfn.data.b1
    Various options may be modified by providing a file pw2casino.dat in outdir with the
following format:

&inputpp
blip_convert=.true.
blip_binary=.true.
blip_single_prec=.false.
blip_multiplicity=1.d0
n_points_for_test=0
/

Some or all of the 5 keywords may be provided, in any order. The default values are as given
above (and these are used if the pw2casino.dat file is not present.
   The meanings of the keywords are as follows:

blip convert : reexpand the converged plane-wave orbitals in localized blip functions prior to
     writing the CASINO wave function file. This is almost always done, since wave functions
     expanded in blips are considerably more efficient in quantum Monte Carlo calculations. If
     blip convert=.false. a pwfn.data file is produced (orbitals expanded in plane waves);
     if blip convert=.true., either a bwfn.data file or a bwfn.data.b1 file is produced,
     depending on the value of blip binary (see below).

blip binary : if true, and if blip convert is also true, write the blip wave function as an un-
     formatted binary bwfn.data.b1 file. This is much smaller than the formatted bwfn.data
     file, but is not generally portable across all machines.

blip single prec : if .false. the orbital coefficients in bwfn.data(.b1) are written out in
     double precision; if the user runs into hardware limits blip single prec can be set to
     .true. in which case the coefficients are written in single precision, reducing the memory
     and disk requirements at the cost of a small amount of accuracy..

blip multiplicity : the quality of the blip expansion (i.e., the fineness of the blip grid) can be
     improved by increasing the grid multiplicity parameter given by this keyword. Increasing
     the grid multiplicity results in a greater number of blip coefficients and therefore larger
     memory requirements and file size, but the CPU time should be unchanged. For very
     accurate work, one may want to experiment with grid multiplicity larger that 1.0. Note,
     however, that it might be more efficient to keep the grid multiplicity to 1.0 and increase
     the plane wave cutoff instead.

n points for test : if this is set to a positive integer greater than zero, PWscf will sample the
     wave function, the Laplacian and the gradient at a large number of random points in the
     simulation cell and compute the overlap of the blip orbitals with the original plane-wave
     orbitals:
                                               < BW |P W >
                                 α= q
                                         < BW |BW >< P W |P W >



                                               11
```
