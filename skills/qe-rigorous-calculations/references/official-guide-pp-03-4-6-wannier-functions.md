# 4.6 Wannier functions

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node11.html
- Retrieved: 2026-07-17T11:52:10+00:00
- Official source SHA-256: `dd71cc417e3bb68038fce6aab8beb5b5844cc29c4d9a02bb8690e97503a280b2`
- Extracted text SHA-256: `0d61a86f8adcf6111801c70557dd3eef4eff899efc619f552f1eb95b59343e24`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.7 Interfaces to/from other code

Up:

4 Usage

Previous:

4.5 Color plot of the

  

Contents

4.6 Wannier functions

There are several Wannier-related utilities in 
PostProc
:

The "Poor Man Wannier" code 
pmw.x
, to be used
in conjunction with DFT+U calculations: see Example 05.

The interface with Wannier90 code, 
pw2wannier.x
:
see the documentation in 
W90/
(you may install the 
Wannier90 plug-in via 
make w90
). For spin-current
matrix elements, implemented in routine 
compute_shc
:
``it writes .sIu and .sHu files used for
WANNIER-BERRI (https://github.com/stepan-tsirkin/wannier-berri/),
and also will be utilized through postw90.x
(https://github.com/manxkim/wannier90/tree/SHC/src) in Wannier90.
In WANNIER-BERRI, .sHu and .sIu files can be used to calculate the
quantity "opt_SHCryoo". In Wannier90, add "berry_task = shc" and
"shc_ryoo=.true.". in the input parameters of postw90.x. They
activate the calculation of SHC using .sHu and .sIu.''

The 
wannier_ham.x
code generates a model Hamiltonian 
in Wannier functions basis: see 
PP/examples/WannierHam_example/
.

The interface with Wannier90 code, 
wannier2pw.x
:
it builds Wannier functions as Hubbard projectors for DFT+U

Note that the 
wfdd.x
code has been moved to 
CP
.
```
