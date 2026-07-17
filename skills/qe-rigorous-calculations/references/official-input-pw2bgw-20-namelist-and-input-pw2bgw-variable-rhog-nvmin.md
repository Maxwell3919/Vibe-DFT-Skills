# INPUT_pw2bgw — NAMELIST: &INPUT_PW2BGW — Variable: rhog_nvmin

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `f66f8d3088bedd9df236481d7d1465a20d492cf2f433aa261e6c600fc1b86b84`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       rhog_nvmin
   
   Type:           INTEGER
   Default:        0
   Description:    index of the lowest band used for calculation of charge density. This is
                   needed if one wants to exclude semicore states from charge density used
                   for the GPP model in sigma code in BerkeleyGW. Make sure to include the
                   same k-points as in scf calculation. Self-consistent charge density is
                   used if rhog_nvmin = 0 and rhog_nvmax = 0. Not used if "rhog_flag" = .FALSE.
                   BEWARE: this feature is highly experimental and may not work at all in
                   parallel, with pools, with spins, etc.
   +--------------------------------------------------------------------
   
```
