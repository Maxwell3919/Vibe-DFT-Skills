# INPUT_HP — NAMELIST: &INPUTHP — Variable: find_atpert

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `f257550ff614f0dc0ce4cb55ea83c4f1adf91da4d6f06d575b013ed32f886879`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       find_atpert
   
   Type:           INTEGER
   Default:        1
   Description:    Method for searching of atoms which must be perturbed.
                   1 = Find how many inequivalent Hubbard atoms there are
                       by analyzing unperturbed occupations.
                   2 = Find how many Hubbard atoms to perturb based on
                       how many different Hubbard atomic types there are.
                       Warning: atoms which have the same type but which
                       are inequivalent by symmetry or which have different
                       occupations will not be distinguished in this case
                       (use option 1 or 3 instead).
                   3 = Find how many inequivalent Hubbard atoms
                       there are using symmetry. Atoms which have the
                       same type but are not equivalent by symmetry will
                       be distinguished in this case.
                   4 = Perturb all Hubbard atoms (the most expensive option)
   +--------------------------------------------------------------------
   
```
