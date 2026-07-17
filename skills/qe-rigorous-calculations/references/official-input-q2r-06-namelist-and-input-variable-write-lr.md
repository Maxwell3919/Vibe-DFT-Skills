# INPUT_Q2R — NAMELIST: &INPUT — Variable: write_lr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt
- Retrieved: 2026-07-17T11:49:50+00:00
- Official source SHA-256: `d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea`
- Extracted text SHA-256: `3fbc245c2061be6f865dc390220b4af1e38303d614c342c49cb1bc862b56c617`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       write_lr
   
   Type:           LOGICAL
   Default:        .false.
   Description:    set to .true. to write long-range IFC into q2r IFC file.
                   This is required when enforcing asr='all' for infrared-
                   active solids in matdyn. An additional column will be written
                   for long-range part of IFC for text format, while a tag named
                   IFC_LR will be created for xml format.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


________________________________________________________________________
* IF file {fildyn}0 does not exist : 

   If a file "fildyn"0 is not found, the code will ignore variable
   "fildyn" and will try to read from the following cards the missing
   information on the q-point grid and file names:
   
   ========================================================================
   Line of input:
   
         nr1 nr2 nr3
      
      
      DESCRIPTION OF ITEMS:
      
         +--------------------------------------------------------------------
         Variables:      nr1, nr2, nr3
         
         Type:           INTEGER
         Description:    dimensions of the FFT grid formed by the q-point grid
         +--------------------------------------------------------------------
         
   ===End of line-of-input=================================================
   
   
   ========================================================================
```
