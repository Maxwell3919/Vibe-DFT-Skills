# INPUT_Q2R — CARD: /////////////////////////////////////////

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt
- Retrieved: 2026-07-17T11:49:50+00:00
- Official source SHA-256: `d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea`
- Extracted text SHA-256: `5f006d484a7c735c0a480815ad4dee4777689def821f6afce23196f76e863ddf`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   CARD:  
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nfile
            file(1)      
            file(2)      
            . . . 
            file(nfile)  
      
      /////////////////////////////////////////
      
      DESCRIPTION OF ITEMS:
      
         +--------------------------------------------------------------------
         Variable:       nfile
         
         Type:           INTEGER
         Description:    number of files containing C(q_n), n=1,"nfile"
         +--------------------------------------------------------------------
         
         +--------------------------------------------------------------------
         Variable:       file
         
         Type:           CHARACTER
         Description:    names of the files containing C(q_n), n=1,"nfile"
                         
                         Note that the name and order of files is not important as
                         long as q=0 is the first.
         +--------------------------------------------------------------------
         
   ===END OF CARD==========================================================
   
   
    
ENDIF
________________________________________________________________________

This file has been created by helpdoc utility on Wed Sep 03 14:23:33 CEST 2025
```
