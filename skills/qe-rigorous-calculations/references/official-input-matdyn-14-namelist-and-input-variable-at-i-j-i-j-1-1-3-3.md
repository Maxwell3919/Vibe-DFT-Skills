# INPUT_MATDYN — NAMELIST: &INPUT — Variable: at(i,j), (i,j)=(1,1) ... (3,3)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `66423928de4466186f5529689480229516afd12a0e1e50d1c53ef738ea1241a0`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       at(i,j), (i,j)=(1,1) ... (3,3)
   
   Type:           REAL
   Description:    supercell lattice vectors - must form a superlattice of the
                   original lattice (default: use original cell)
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      l1, l2, l3
   
   Type:           INTEGER
   Description:    supercell lattice vectors are original cell vectors times
                   l1, l2, l3 respectively (default: 1, ignored if "at" specified)
   +--------------------------------------------------------------------
   
```
