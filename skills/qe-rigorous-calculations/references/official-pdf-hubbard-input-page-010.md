# Hubbard_input.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `68dd7cfc1c93f74d36bc14cb4e17a93823c58c3f77751165ab9d0f3b074165af`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
The meaning of Hubbard J(i,ityp) was the following (i runs from 1 to 3, and ityp is the
atomic type):
    For p orbitals: J = Hubbard J(1,ityp);

    For d orbitals: J = Hubbard J(1,ityp), B = Hubbard J(2,ityp);

    For f orbitals: J = Hubbard J(1,ityp), E2 = Hubbard J(2,ityp), E3 = Hubbard J(3,ityp)
     ;
(If B or E2 or E3 were not specified or set to 0 they were calculated from J using atomic ratios.)

   Where these name conventions come from? There are many possible choices how to parametrize
Hubbard interactions: i) Slater integrals F 0 , F 2 , F 4 , ..., ii) standard Racah parameters A, B,
C, D, ..., iii) another set of Racah parameters E 0 , ..., E 3 , iv) more physical choice U and J plus
other missing like B for the d shell or E 2 and E 3 for the f shell. In Quantum ESPRESSO
the latter notation is used. Check the following references for further reading [2, 7, 8, 9, 10, 11].

Below is the example of the new input syntax of DFT+U +J (Liechtenstein’s formulation) for
Ni2MnGa:
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
 Mn 0.0000000000   0.0000000000   0.0000000000
 Ni 0.5000000000   0.7500000000   0.2500000000
 Ni 0.5000000000   0.2500000000   0.7500000000
 Ga 0.0000000000   0.5000000000   0.5000000000
K_POINTS (automatic)

                                                10
```
