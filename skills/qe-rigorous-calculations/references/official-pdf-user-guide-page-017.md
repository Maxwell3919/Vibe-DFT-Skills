# user_guide.pdf — page 17

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `0f004fd0d820a03c43fdec7f790220f7bd53a4da967f170f1ca73ac33afa1435`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.6.2   Usage
In order to use libxc functionals, you can enforce them from input by including the input dft
string in the system namelist. Starting from v7.0 of Quantum ESPRESSO the only allowed
notation for DFTs that include Libxc terms is the index one. For example, to use the libxc
version of the PBE functional (both exchange and correlation):
input_dft = ‘XC-000I-000I-101L-130L-000I-000I’
The letters I or L next to each ID stand for Internal and libxc. This is equivalent to the old
full-name notation:
input_dft = ‘gga_x_pbe gga_c_pbe’           ***OLD***
The order must be the usual one, namely LDA exchange, LDA correlation, GGA exchange,
GGA correlation, MGGA exchange, MGGA correlation. libxc exchange+correlation function-
als can be put in the exchange or in the correlation slot with no difference.
The reason why the full-name notation has been disabled is to eliminate the risk of overlaps
among different names (occurring especially when combinations of internal and libxc DFTs
are used).
The complete list of libxc functionals and IDs is available at: https://libxc.gitlab.io/.
Combinations of Quantum ESPRESSO and libxc functionals are allowed in PW, but some
attention has to be paid to their reciprocal compatibility (see section below).
For example, the internal exchange term of PBE together with the correlation term of PBE in
libxc is obtained by:
input_dft = ‘XC-001I-000I-003I-130L-000I-000I’
which corresponds to the old:
input_dft = ‘sla pbx gga_c_pbe’          ***OLD***
Note that when using GGA internal functionals you must always specify the LDA term too,
while it is not the case for the libxc ones.
Abbreviations are allowed when zero tails are present. The above example is still valid by
putting:
input_dft = ‘XC-001I-000I-003L-130L’
since no MGGA terms are present.
Non-local terms can be included by just adding their name after the index notation, for example:
input_dft=‘XC-001i-004i-013i-vdw2’

2.6.3   Differences between Libxc and internal functionals
There are some differences between Quantum ESPRESSO functionals and libxc ones. In
Quantum ESPRESSO the LDA and the GGA terms are separated and must be specified
independently. In libxc the GGA functionals already include the LDA part (Slater exchange
and Perdew&Wang correlation in most of the cases with the exception, for example, of Lee
Yang Parr functionals).
The libxc metaGGA functionals may or may not need the LDA and GGA terms, depending

                                              17
```
