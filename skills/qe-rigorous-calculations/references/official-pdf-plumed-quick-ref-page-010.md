# plumed_quick_ref.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `ad50098477d4d16eb6dc5e9b4711fc12b79e58ac39e33233504501be9d8bdd09`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
|-HILLS:
|--HEIGHT 0.001000      WRITING STRIDE 2 DEPOSITION RATE 0.000025

|-PRINTING ON COLVAR FILE EVERY 1 STEPS
|-INITIAL TIME OFFSET IS 0.000000 TIME UNITS

1-DISTANCE: (1st SET: 1 ATOMS), (2nd SET: 1 ATOMS);              PBC ON SIGMA 0.300000
|- DISCARDING DISTANCE COMPONENTS (XYZ): 000
|- 1st SET MEMBERS: 1
|- 2nd SET MEMBERS: 3


2-DISTANCE: (1st SET: 1 ATOMS), (2nd SET: 1 ATOMS);              PBC ON SIGMA 0.300000
|- DISCARDING DISTANCE COMPONENTS (XYZ): 000
|- 1st SET MEMBERS: 2
|- 2nd SET MEMBERS: 3

|-WALL ON COLVAR 1: UPPER LIMIT = 7.000000, KAPPA = 100.000000, EXPONENT = 4,
 REDUX = 1.000000, OFFSET = 0.000000

|-WALL ON COLVAR 1: LOWER LIMIT = 2.500000, KAPPA = 100.000000, EXPONENT = 4,
 REDUX = 1.000000, OFFSET = 0.000000

|-WALL ON COLVAR 2: UPPER LIMIT = 7.000000, KAPPA = 100.000000, EXPONENT = 4,
 REDUX = 1.000000, OFFSET = 0.000000

|-WALL ON COLVAR 2: LOWER LIMIT = 2.500000, KAPPA = 100.000000, EXPONENT = 4,
 REDUX = 1.000000, OFFSET = 0.000000

|-HILLS ACTIVE ON COLVAR 1
|-HILLS ACTIVE ON COLVAR 2
   This tells you that everything is going fine. The index of atoms are parsed correctly
and the printout is correctly understood. Now what you get is a COLVAR file that
consists in the time evolution of the CVs. Its format looks something like this:
#! FIELDS time cv1 cv2 vbias vwall vext
     0.000      3.470115309      5.828643634                 0.000000000          0.000000000
                0.000000000      0.000000000                 0.000000000
    20.000      3.476912892      5.822800771                 0.000000000          0.000000000
                0.000000000      0.000000000                 0.000000000
    40.000      3.483516729      5.817608411                 0.001000000          0.000000000
                0.000000000      0.000000000                 0.000000000
    60.000      3.490411466      5.812574439                 0.000999600          0.000000000
                0.000000000      0.000000000                 0.000000000
    80.000      3.498291622      5.807005696                 0.001998170          0.000000000
                0.000000000      0.000000000                 0.000000000

                                          10
```
