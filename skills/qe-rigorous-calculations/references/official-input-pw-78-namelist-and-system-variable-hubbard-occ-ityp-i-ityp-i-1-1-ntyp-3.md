# INPUT_PW — NAMELIST: &SYSTEM — Variable: Hubbard_occ(ityp,i), (ityp,i)=(1,1) ... (ntyp,3)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `83e976fa5eb39f2e69ddf43870d1b78bce86e0b82f9ffa61ebb1f65c9701c761`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       Hubbard_occ(ityp,i), (ityp,i)=(1,1) ... (ntyp,3)
   
   Type:           REAL
   Default:        read from pseudopotentials
   Description:    Hubbard occupations is the number of electrons in the
                   Hubbard manifold. By default they are initialized by
                   reading the occupations from pseudopotentials. If specified
                   from the input, then the values read from the pseudopotentials
                   will be overwritten.
                   The second index of the Hubbard_occ array corresponds to the
                   Hubbard manifold number. It is possible to specify up to
                   three Hubbard manifolds per Hubbard atom. However, if you want
                   to specify three manifolds then the second and the third manifolds
                   will be considered as one effective manifold (see Doc/Hubbard_input.pdf)
   +--------------------------------------------------------------------
   
```
