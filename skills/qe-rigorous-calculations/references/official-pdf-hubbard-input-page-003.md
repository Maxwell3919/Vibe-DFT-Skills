# Hubbard_input.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `e4c1601ace947df8c80a6f95c1484d77dd74ec58d3c8dbb0364bcb489cf3fa23`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3     New DFT+Hubbard input
In this section we present the new DFT+Hubbard input syntax that replaces the old one
starting from Quantum ESPRESSO 7.3.1. Let us give examples for different flavors of
DFT+Hubbard.

3.1    DFT+U (Dudarev’s formulation)
Important notice: The Hubbard U values shown in the examples below are random values
chosen just for the sake of demonstration purposes and they must not be used for production
calculations.

In the past, to use this case the user had to specify in the pw.x input file e.g. the following:

    &system
       ...
       lda_plus_u = .true.
       lda_plus_u_kind = 0
       U_projection_type = ’ortho-atomic’
       Hubbard_U(1) = 5.0
       Hubbard_U(2) = 6.0
    /

Below is the example of the new input syntax of DFT+U (Dudarev’s formulation) for Ni2MnGa:

&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’Ni2MnGa’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 7, celldm(1) = 7.80, celldm(3) = 1.4142136,
    nat = 4, ntyp = 3, ecutwfc = 50.0, ecutrho = 400.0, nspin = 2,
    occupations =’smearing’, smearing =’mv’, degauss = 0.01,
    starting_magnetization(1) = 0.5,
    starting_magnetization(2) = 0.5
 /
 &electrons
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Mn 54.938 Mn.pbesol-spn-rrkjus_psl.0.3.1.UPF
 Ni 58.693 Ni.pbesol-n-rrkjus_psl.0.1.UPF
 Ga 69.723 Ga.pbesol-dn-rrkjus_psl.0.2.UPF
ATOMIC_POSITIONS (crystal)


                                                3
```
