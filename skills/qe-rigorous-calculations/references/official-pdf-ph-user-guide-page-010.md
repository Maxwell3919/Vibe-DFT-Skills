# ph_user_guide.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `17f280ac6d222dfde223a60e5dc2745ef854e1c3bd3836ea8341009ec553690e`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
ph.x does not yield acoustic modes with zero frequency at q = 0 This may not be
an error: the Acoustic Sum Rule (ASR) is never exactly verified, because the system is never
exactly translationally invariant as it should be. The calculated frequency of the acoustic mode
is typically less than 10 cm−1 , but in some cases it may be much higher, up to 100 cm−1 . The
ultimate test is to diagonalize the dynamical matrix with program dynmat.x, imposing the
ASR. If you obtain an acoustic mode with a much smaller ω (let us say < 1cm−1 ) with all
other modes virtually unchanged, you can trust your results.
    “The problem is [...] in the fact that the XC energy is computed in real space on a discrete
grid and hence the total energy is invariant (...) only for translation in the FFT grid. Increasing
the charge density cutoff increases the grid density thus making the integral more exact thus
reducing the problem, unfortunately rather slowly...This problem is usually more severe for
GGA than with LDA because the GGA functionals have functional forms that vary more
strongly with the position; particularly so for isolated molecules or system with significant
portions of “vacuum” because in the exponential tail of the charge density a) the finite cutoff
(hence there is an effect due to cutoff) induces oscillations in rho and b) the reduced gradient
is diverging.”(info by Stefano de Gironcoli, June 2008)

ph.x yields really lousy phonons, with bad or “negative” frequencies or wrong
symmetries or gross ASR violations Possible reasons:

    if this happens only for acoustic modes at q = 0 that should have ω = 0: Acoustic Sum
     Rule violation, see the item before this one.

    wrong data file read.

    wrong atomic masses given in input will yield wrong frequencies (but the content of file
     fildyn should be valid, since the force constants, not the dynamical matrix, are written
     to file).

    convergence threshold for either SCF (conv thr) or phonon calculation (tr2 ph) too large:
     try to reduce them.

    maybe your system does have negative or strange phonon frequencies, with the approx-
     imations you used. A negative frequency signals a mechanical instability of the chosen
     structure. Check that the structure is reasonable, and check the following parameters:

        – The cutoff for wavefunctions, ecutwfc
        – For USPP and PAW: the cutoff for the charge density, ecutrho
        – The k-point grid, especially for metallic systems.

    For metallic systems: it has been observed that the convergence with respect to the
     k-point grid and smearing is very slow in presence of semicore states, and for phonon
     wave-vectors that are not commensurate i with the k-point grid (that is, q 6= ki − kj )

Note that “negative” frequencies are actually imaginary: the negative sign flags eigenvalues of
the dynamical matrix for which ω 2 < 0.




                                                10
```
