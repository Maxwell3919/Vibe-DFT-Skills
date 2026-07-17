# INPUT_PW — NAMELIST: &SYSTEM — Variable: celldm(i), i=1,6

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d0989906d5bdbd21ea47b1f5f08ca5b6dd8c9c553c56d928691f8dc43d6cd61e`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       celldm(i), i=1,6
      
      Type:           REAL
      See:            ibrav
      Description:    Crystallographic constants - see the "ibrav" variable.
                      Specify either these OR "A","B","C","cosAB","cosBC","cosAC" NOT both.
                      Only needed values (depending on "ibrav") must be specified
                      alat = "celldm"(1) is the lattice parameter "a" (in BOHR)
                      If "ibrav"==0, only "celldm"(1) is used if present;
                      cell vectors are read from card "CELL_PARAMETERS"
      +--------------------------------------------------------------------
      
      OR:
      
      +--------------------------------------------------------------------
      Variables:      A, B, C, cosAB, cosAC, cosBC
      
      Type:           REAL
      See:            ibrav
      Description:    Traditional crystallographic constants:
                      
                        a,b,c in ANGSTROM
                        cosAB = cosine of the angle between axis a and b (gamma)
                        cosAC = cosine of the angle between axis a and c (beta)
                        cosBC = cosine of the angle between axis b and c (alpha)
                      
                      The axis are chosen according to the value of "ibrav".
                      Specify either these OR "celldm" but NOT both.
                      Only needed values (depending on "ibrav") must be specified.
                      
                      The lattice parameter alat = A (in ANGSTROM ).
                      
                      If "ibrav" == 0, only A is used if present, and
                      cell vectors are read from card "CELL_PARAMETERS".
      +--------------------------------------------------------------------
      
   \\\---
   
```
