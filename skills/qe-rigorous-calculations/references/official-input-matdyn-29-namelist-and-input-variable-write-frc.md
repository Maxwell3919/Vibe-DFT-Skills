# INPUT_MATDYN — NAMELIST: &INPUT — Variable: write_frc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `8677ab18062291f65671fed251f4ed718f5dc6667192cf313020a74051c52d0c`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       write_frc
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true. write force constants with "asr" imposed into file.
                   The filename would be "flfrc"+".matdyn". The long-range part of
                   force constants will be not written.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


________________________________________________________________________
* IF readtau == .true. : 

   ========================================================================
```
