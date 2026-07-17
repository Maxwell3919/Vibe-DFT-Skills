# INPUT_PW — NAMELIST: &SYSTEM — Variable: block

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `8015cb0b5b8ae611e9a329da7c34a59f6ab8f1b127914430b10f95d6925a1d44`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       block
      
      Type:           LOGICAL
      Default:        .FALSE.
      Description:    used only if "gate" = .TRUE.
                      Adds a potential barrier to the total potential seen by the
                      electrons to mimic a dielectric in field effect configuration
                      and/or to avoid electrons spilling into the vacuum region for
                      electron doping. Potential barrier is from "block_1" to "block_2" and
                      has a height of block_height.
                      If "dipfield" = .TRUE. then "eopreg" is used for a smooth increase and
                      decrease of the potential barrier.
      +--------------------------------------------------------------------
      
```
