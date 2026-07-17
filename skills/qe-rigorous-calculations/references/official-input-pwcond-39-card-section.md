# INPUT_PWCOND — CARD: /////////////////////////////////////////

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `4345051ec3622642084f3d60f594dbb0d74368ca3e76e745cc5a6b97e11a0eea`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD:  

   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
         nkpts
         kx(1)      ky(1)      weight(1)      
         kx(2)      ky(2)      weight(2)      
         . . . 
         kx(nkpts)  ky(nkpts)  weight(nkpts)  
         nenergy
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       nkpts
      
      Type:           INTEGER
      Description:    Number of k_\perp points
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      kx, ky, weight
      
      Type:           REAL
      Description:    k-point coordinates and weights
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       nenergy
      
      Type:           INTEGER
      Description:    number of energy points
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


This file has been created by helpdoc utility on Wed Sep 03 14:29:26 CEST 2025
```
