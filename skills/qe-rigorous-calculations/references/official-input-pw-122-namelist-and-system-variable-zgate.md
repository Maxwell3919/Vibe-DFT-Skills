# INPUT_PW — NAMELIST: &SYSTEM — Variable: zgate

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `935e1b5f610f94a803bf96175a3680d86036740b4d7c26c07043627d387e61fd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       zgate
      
      Type:           REAL
      Default:        0.5
      Description:    used only if "gate" = .TRUE.
                      Specifies the position of the charged plate which represents
                      the counter charge in doped systems ("tot_charge" .ne. 0).
                      In units of the unit cell length in z direction, "zgate" in ]0,1[
                      Details of the gate potential can be found in
                      T. Brumme, M. Calandra, F. Mauri; PRB 89, 245406 (2014).
      +--------------------------------------------------------------------
      
```
