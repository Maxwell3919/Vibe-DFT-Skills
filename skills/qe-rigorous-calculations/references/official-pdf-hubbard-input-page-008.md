# Hubbard_input.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `ae3842f9800cb8b0f0388999e3afec8926231cd681fe07553311fb3c83ae49b0`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Mn 54.938 Mn.pbesol-spn-rrkjus_psl.0.3.1.UPF
 Ni 58.693 Ni.pbesol-n-rrkjus_psl.0.1.UPF
 Ga 69.723 Ga.pbesol-dn-rrkjus_psl.0.2.UPF
ATOMIC_POSITIONS (crystal)
 Mn 0.0000000000   0.0000000000 0.0000000000
 Ni 0.5000000000   0.7500000000 0.2500000000
 Ni 0.5000000000   0.2500000000 0.7500000000
 Ga 0.0000000000   0.5000000000 0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
U Mn-3d    5.0
U Mn-3p-3s 3.0
U Ni-3d    6.0
U Ni-4s    2.0
In this example, Hubbard occ(1,1) corresponds to the occupations of Mn-3d states,
Hubbard occ(1,2) corresponds to the occupations of Mn-3p states, and
Hubbard occ(1,3) corresponds to the occupations of Mn-3s states. Similarly,
Hubbard occ(2,1) corresponds to the occupations of Ni-3d states, and
Hubbard occ(2,2) corresponds to the occupations of Ni-4s states.

Below is the example showing how to perform DFT+U +J0 calculation:
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

                                            8
```
