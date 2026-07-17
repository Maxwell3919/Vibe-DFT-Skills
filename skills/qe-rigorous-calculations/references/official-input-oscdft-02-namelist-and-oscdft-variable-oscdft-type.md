# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: oscdft_type

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `b107eb3ed21d598202e4d52f98ba7e71990a3ea45b6b8a0184324992a487a9ca`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       oscdft_type
   
   Type:           INTEGER
   Default:        1
   Description:    1 : C. Ku, P. H. L. Sit, J. Chem. Theory Comput. 15, 4781 (2019).
                   2 : L. Ponet, E. Di Lucente, N. Marzari, npj Comput. Mater. 10, 151 (2024).
                   
                   Note: For oscdft_type=2, only the keyword "occupation" and the keywords
                         constraint_* can be used (see below).
   +--------------------------------------------------------------------
   
```
