# INPUT_HP — NAMELIST: &INPUTHP — Variable: lmin

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `d4b30f55fc80d3aad1c655a8ec6c39e2760c92cb6feda9674833e6b44c80ba9f`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lmin
   
   Type:           INTEGER
   Default:        2
   Description:    Minimum value of the orbital quantum number of the Hubbard
                   atoms starting from which (and up to the maximum l in the
                   system) Hubbard V will be written to the file parameters.out.
                   "lmin" refers to the orbital quantum number of the atom
                   corresponding to the first site-index in Hubbard_V(:,:,:).
                   This keyword is used only for DFT+U+V and only
                   in the post-processing stage. Example: "lmin"=1 corresponds to
                   writing to file V between e.g. oxygen (with p states) and its
                   neighbors, and including V between transition metals (with d
                   states) and their neighbors. Instead, when "lmin"=2 only the
                   latter will be written to parameters.out.
   +--------------------------------------------------------------------
   
```
