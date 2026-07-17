# Hubbard_input.pdf — page 12

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `fbaa58f3feda732e4edc3ce178dbf0cceaecb25de1e51b463cab38261aac8d49`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Standard orbitals correspond to the main Hubbard channel (e.g. d electrons in transition met-
als) and background orbitals correspond to the secondary Hubbard channel (e.g. p electrons in
transition metals).

The second index of Hubbard V(na,nb,k) (i.e. the index nb) corresponds to atoms that are
neighbors to atom na. You can notice that nb can take quite large values (even larger than
the total number of atoms in the simulation cell). This is so because we are using periodic
boundary conditions and hence some neighbors fall outside of our simulation cell. For this rea-
son, the code generates virtual cells around our real cells. This way we can find all neighbors.
In practice, this is achieved by constructing a virtual 3 × 3 × 3 supercell and by replicating
atoms. This is why the indices of neighboring atoms are so strange. If you are interested how
these indices are generated, please check the subroutine PW/src/intersiteV.f90. A priori, it
is not obvious how to find the indices of neighbors. For this reason you can use the hp.x code
of Quantum ESPRESSO that will determine the values of U and V and the indices of couples.

In the new input, the same logic holds but the input syntax has changed. Below is the example
of the new input syntax of DFT+U +V (Dudarev’s formulation) for LiCoO2 :

&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’LiCoO2’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 5, celldm(1) = 9.3705, celldm(4) = 0.83874,
    nat = 4, ntyp = 3, ecutwfc = 50.0, ecutrho = 400.0
 /
 &electrons
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Co 59.0     Co.pbesol-spn-rrkjus_psl.0.3.1.UPF
 O   16.0   O.pbesol-n-rrkjus_psl.0.1.UPF
 Li   7.0   Li.pbesol-s-rrkjus_psl.0.2.1.UPF
ATOMIC_POSITIONS (crystal)
 Co 0.0000000000     0.0000000000   0.0000000000
 O   0.2604885000    0.2604885000   0.2604885000
 O   0.7395115000    0.7395115000   0.7395115000
 Li 0.5000000000     0.5000000000   0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
U Co-3d 7.70
V Co-3d O-2p 1 19 0.75


                                              12
```
