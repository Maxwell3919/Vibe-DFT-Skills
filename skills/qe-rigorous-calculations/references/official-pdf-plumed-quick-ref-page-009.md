# plumed_quick_ref.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `e785e2d1ecbaa50e7f2df1d0ce05cc752000f20e66b5bd8670a92ee7bd5a99ad`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
     celldm(2) = 0.666666d0,
     celldm(3) = 0.666666d0,
     nat = 6,
     ntyp = 3,
     tot_charge = -1,
     ecutwfc = 25.0,
     ecutrho = 100.0,
     nr1b = 24, nr2b = 24, nr3b = 24,
     nosym = .true.
 /

 &electrons
    conv_thr = 1.0d-8
    mixing_beta = 0.7
 /
 &ions
    pot_extrapolation=’second-order’
    wfc_extrapolation=’second-order’
    ion_temperature=’berendsen’
    tempw= 300.
    nraise=20
 /
ATOMIC_SPECIES
 Cl 35.4527d0 Cl.blyp-mt.UPF
 C 12.0107d0 C.blyp-mt.UPF
 H 1.00794d0 H.blyp-vbc.UPF

ATOMIC_POSITIONS bohr
Cl      12.880706242        6.000000000        5.994035868
Cl       3.581982751        6.000000000        5.989431927
C        9.410606817        6.000000000        6.004535337
H        8.743333410        4.313700292        5.030609604
H        8.743333410        7.686299708        5.030609604
H        8.746264064        6.000000000        7.952930073

K_POINTS gamma

   In this example, we perform a 2000 steps NVT MD to reconstruct the free energy
profile for the SN2 reaction. To run the metadynamics simulation, simply type

pw.x -plumed < pw.in > pw.out

    After the execution of the program, you will get a brunch of interesting stuff. First
of all, you will get a PLUMED.OUT file that contains some printout from PLUMED so you
may check whether the input was correctly read:

::::::::::::::::: READING PLUMED INPUT :::::::::::::::::

                                           9
```
