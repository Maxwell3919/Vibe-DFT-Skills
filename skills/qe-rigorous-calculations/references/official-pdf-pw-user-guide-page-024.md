# pw_user_guide.pdf — page 24

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `20077b870d333c8b176b11b67b023972080c4c888e7f74200b78912ead2b89e3`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    the Fermi energy is found by bisection assuming that the integrated DOS N (E) is an
     increasing function of the energy. This is not guaranteed for Methfessel-Paxton smearing
     of order 1 and can give problems when very few k-points are used. Use some other
     smearing function: simple Gaussian broadening or, better, Marzari-Vanderbilt-DeVita-
     Payne ’cold smearing’.

pw.x yields internal error: cannot bracket Ef message but does not stop This may
happen under special circumstances when you are calculating the band structure for selected
high-symmetry lines. The message signals that occupations and Fermi energy are not correct
(but eigenvalues and eigenvectors are). Remove occupations=’tetrahedra’ in the input data
to get rid of the message.

pw.x runs but nothing happens Possible reasons:

    in parallel execution, the code died on just one processor. Unpredictable behavior may
     follow.

    in serial execution, the code encountered a floating-point error and goes on producing
     NaNs (Not a Number) forever unless exception handling is on (and usually it isn’t). In
     both cases, look for one of the reasons given above.

    maybe your calculation will take more time than you expect.

pw.x yields weird results If results are really weird (as opposed to misinterpreted):

    if this happens after a change in the code or in compilation or preprocessing options, try
     make clean, recompile. The make command should take care of all dependencies, but do
     not rely too heavily on it. If the problem persists, recompile with reduced optimization
     level.

    maybe your input data are weird.

FFT grid is machine-dependent Yes, they are! The code automatically chooses the small-
est grid that is compatible with the specified cutoff in the specified cell, and is an allowed value
for the FFT library used. Most FFT libraries are implemented, or perform well, only with
dimensions that factors into products of small numbers (2, 3, 5 typically, sometimes 7 and 11).
Different FFT libraries follow different rules and thus different dimensions can result for the
same system on different machines (or even on the same machine, with a different FFT). See
function allowed in FFTXlib/fft support.f90.
    As a consequence, the energy may be slightly different on different machines. The only
piece that explicitly depends on the grid parameters is the XC part of the energy that is
computed numerically on the grid. The differences should be small, though, especially for LDA
calculations.
    Manually setting the FFT grids to a desired value is possible, but slightly tricky, using
input variables nr1, nr2, nr3 and nr1s, nr2s, nr3s. The code will still increase them if not
acceptable. Automatic FFT grid dimensions are slightly overestimated, so one may try very
carefully to reduce them a little bit. The code will stop if too small values are required, it will
waste CPU time and memory for too large values.

                                                24
```
