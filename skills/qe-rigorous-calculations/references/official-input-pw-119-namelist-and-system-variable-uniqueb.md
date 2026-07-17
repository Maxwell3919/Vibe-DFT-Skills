# INPUT_PW — NAMELIST: &SYSTEM — Variable: uniqueb

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `20da3f3faa0440dd2e2ffd3f9176c68bf995148721836525f6e51158d8e3ea7d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       uniqueb
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    Used only for monoclinic lattices. If .TRUE. the b
                   unique "ibrav" (-12 or -13) are used, and symmetry
                   equivalent positions are chosen assuming that the
                   twofold axis or the mirror normal is parallel to the
                   b axis. If .FALSE. it is parallel to the c axis.
   +--------------------------------------------------------------------
   
```
