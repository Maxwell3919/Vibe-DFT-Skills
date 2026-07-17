# INPUT_kcw — NAMELIST: &CONTROL — Variable: spin_component

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `c8f52087d9f3998298c38329ca805400364f73be4c29e0ccc647610b38fec62a`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       spin_component
   
   Type:           INTEGER
   Default:        1
   Description:    Which spin channel to calculate (only collinear calculation).
                   1 = spin up channel
                   2 = spin down channel
                   It has to be consistent with the previous Wannier90
                   calculation (see 'spin' keyword in Wannier90 documentation)
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      mp1, mp2, mp3
   
   Type:           INTEGER
   Default:        -1,-1,-1
   Description:    Parameters of the Monkhorst-Pack grid (no offset).
                   Same meaning as for nk1, nk2, nk3 in the input of pw.x.
                   It has to coincide with the regular mesh used for the
                   wannier90 calculation.
   +--------------------------------------------------------------------
   
```
