# pw_user_guide.pdf — page 21

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `9b3b3e0a4b75e847e7cb390e19f9aa50c836df88e67d95ee35619d4a0379269d`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    Input files should be plain ASCII text. The presence of CRLF line terminators (may
     appear as ˆM, Control-M, characters at the end of lines), tabulators, or non-ASCII char-
     acters (e.g. non-ASCII quotation marks, that at a first glance may look the same as the
     ASCII character) is a frequent source of trouble. Typically, this happens with files coming
     from Windows or produced with ”smart” editors. Verify with command file and convert
     with command iconv if needed.

    The input file ends at the last character (there is no end-of-line character).

    Out-of-bound indices in dimensioned variables read in the namelists.

These reasons may cause the code to crash with rather mysterious error messages. If none of
the above applies and the code stops at the first namelist (&CONTROL) and you are running
in parallel, see the previous item.

pw.x mumbles something like cannot recover or error reading recover file You are
trying to restart from a previous job that either produced corrupted files, or did not do what
you think it did. No luck: you have to restart from scratch.

pw.x stops with inconsistent DFT error As a rule, the flavor of DFT used in the
calculation should be the same as the one used in the generation of pseudopotentials, which
should all be generated using the same flavor of DFT. This is actually enforced: the type of
DFT is read from pseudopotential files and it is checked that the same DFT is read from all
PPs. If this does not hold, the code stops with the above error message. Use – at your own
risk – input variable input dft to force the usage of the DFT you like.

pw.x stops with error in cdiaghg or rdiaghg Possible reasons for such behavior are not
always clear, but they typically fall into one of the following cases:

    serious error in data, such as bad atomic positions or bad crystal structure/supercell;

    a bad pseudopotential, typically with a ghost, or a USPP giving non-positive charge
     density, leading to a violation of positiveness of the S matrix appearing in the USPP
     formalism;

    a failure of the algorithm performing subspace diagonalization. The LAPACK algorithms
     used by cdiaghg (for generic k-points) or rdiaghg (for Γ−only case) are very robust and
     extensively tested. Still, it may seldom happen that such algorithms fail. Try to use
     conjugate-gradient diagonalization (diagonalization=’cg’), a slower but very robust
     algorithm, and see what happens; or, newer diagonalization ’paro’.

    buggy libraries. Machine-optimized mathematical libraries are very fast but sometimes
     not so robust from a numerical point of view. Suspicious behavior: you get an error that
     is not reproducible on other architectures or that disappears if the calculation is repeated
     with even minimal changes in parameters. Try to use compiled BLAS and LAPACK (or
     better, ATLAS) instead of machine-optimized libraries.




                                               21
```
