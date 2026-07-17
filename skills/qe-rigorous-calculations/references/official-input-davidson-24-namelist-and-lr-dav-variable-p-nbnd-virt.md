# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: p_nbnd_virt

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `f648783eca1ef15ee95b9a58a0b2cc63ff566f296d91733e93436ca3a5df92e4`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       p_nbnd_virt
   
   Type:           INTEGER
   Default:        10
   Description:    Number of empty states selected from the total number
                   of empty states computed by PWscf. This variable is
                   useful if there are too many empty states but your
                   are interested in only some of them.
                   In priciple this variable and "p_nbnd_occ" affect only
                   the interpretation of the eigenstates, but do not effect
                   their energy and the final absorption spectrum.
                   Make sure that min(p_nbnd_occ,nbnd_occ)*min(p_nbnd_virt,nbnd_virt)
                   is lager than the number of initial vectors ("num_init"),
                   so you will not end up using random trial vectors which would
                   slow down the convergence.
   +--------------------------------------------------------------------
   
```
