# INPUT_PW — NAMELIST: &SYSTEM — Variable: relaxz

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `17d6ecef096bbb7e0f84ebebb56592dc478c1da52cc72c4b5adc20ffb69fd550`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       relaxz
      
      Type:           LOGICAL
      Default:        .FALSE.
      Description:    used only if "gate" = .TRUE.
                      Allows the relaxation of the system towards the charged plate.
                      Use carefully and utilize either a layer of fixed atoms or a
                      potential barrier ("block"=.TRUE.) to avoid the atoms moving to
                      the position of the plate or the dipole of the dipole
                      correction ("dipfield"=.TRUE.).
      +--------------------------------------------------------------------
      
```
